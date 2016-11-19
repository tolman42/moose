import os
import sys
import copy
import multiprocessing
import markdown
import markdown_include
import bs4
import shutil
from distutils.dir_util import copy_tree
import logging
log = logging.getLogger(__name__)

import MooseDocs
from MooseDocs.extensions.MooseMarkdown import MooseMarkdown
from NavigationNode import NavigationNode
from MoosePage import MoosePage


def build_options(parser, subparser):
  """
  Command-line options for build command.
  """
  build_parser = subparser.add_parser('build', help='Generate and Build the documentation for serving.')
  build_parser.add_argument('--disable-threads', action='store_true', help="Disable threaded building.")
  return build_parser


def make_tree(directory, node, *args):
  """
  Create the tree structure of NavigationNode/MoosePage objects
  """
  for p in os.listdir(directory):

    path = os.path.join(directory, p)
    if p in ['index.md', 'index.html']:
      continue

    if os.path.isfile(path) and (path.endswith('.md') or path.endswith('.html')):
      child = MoosePage(path, node, *args)
      node.children.append(child)

    elif os.path.isdir(path) and (p not in ['.', '..']):
      md = os.path.join(path, 'index.md')
      html = os.path.join(path, 'index.html')
      if os.path.exists(md):
        child = MoosePage(md, node, *args)
      elif os.path.exists(html):
        child = MoosePage(html, node, *args)
      else:
        child = NavigationNode(path, node, *args)

      make_tree(path, child, *args)
      node.children.append(child)

def flat(node):
  """
  Create a flat list of pages for parsing and generation.

  Args:
    node[NavigationNode]: The root node to flatten from
  """
  for child in node.children:
    if isinstance(child, MoosePage):
      yield child
    for c in flat(child):
      yield c

class Builder(object):
  """
  Object for building
  """
  def __init__(self, parser, site_dir, template, template_args, navigation):

    self._parser = parser
    self._site_dir = site_dir

    self._template = template
    self._template_args = template_args

    self._navigation = MooseDocs.yaml_load(navigation)

    # Extract the MooseLinkDatabase for creating source and doxygen links
    self._syntax = dict()
    for ext in parser.registeredExtensions:
      if isinstance(ext, MooseMarkdown):
        self._syntax = ext.syntax
        break

    content_dir = os.path.join(os.getcwd(), 'content')
    self._root = MoosePage(path=os.path.join(content_dir, 'index.md'), site_dir=self._site_dir, syntax=self._syntax)
    make_tree(content_dir, self._root, self._site_dir, self._syntax)

    self._pages = [self._root] + list(flat(self._root))

  def __iter__(self):
    """
    Allow direct iteration over pages contained in this object.
    """
    return self._pages.__iter__()


  def build(self, disable_threads=False):
    """
    Build all the pages in parallel.
    """

    if disable_threads:
      for page in self._pages:
        page.build(self._parser, self._navigation, self._template, self._template_args)

    else:
      jobs = []
      for page in self._pages:
        func = lambda: page.build(self._parser, self._navigation, self._template, self._template_args)
        p = multiprocessing.Process(target=func)
        p.start()
        jobs.append(p)

      for job in jobs:
        job.join()

      self.copyFiles()


  def copyFiles(self):
    """
    Copy the css/js/fonts/media files for this project.
    """

    def helper(src, dst):
      if not os.path.exists(dst):
        os.makedirs(dst)
      if os.path.exists(src):
        copy_tree(src, dst)

    # Copy js/css/media from MOOSE and current projects
    for from_dir in [os.path.join(MooseDocs.MOOSE_DIR, 'docs'), os.getcwd()]:
      helper(os.path.join(from_dir, 'js'), os.path.join(self._site_dir, 'js'))
      helper(os.path.join(from_dir, 'css'), os.path.join(self._site_dir, 'css'))
      helper(os.path.join(from_dir, 'media'), os.path.join(self._site_dir, 'media'))


def build(config_file='moosedocs.yml', disable_threads=False, **kwargs):
  """
  The main build command.
  """

  # Load the YAML configuration file
  config = MooseDocs.load_config(config_file, **kwargs)

  # Create the markdown parser
  extensions, extension_configs = MooseDocs.get_markdown_extensions(config)
  parser = markdown.Markdown(extensions=extensions, extension_configs=extension_configs)

  # Create object for storing pages to be generated
  builder = Builder(parser, config['site_dir'], config['template'], config['template_arguments'], config['navigation'])

  # Create the html
  builder.build(disable_threads=disable_threads)
  return config, parser, builder
