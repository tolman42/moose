import os
import sys
import re
import subprocess
import markdown
import collections
import yaml
import logging
log = logging.getLogger(__name__)

from MooseObjectSyntax import MooseObjectSyntax
from MooseSystemSyntax import MooseSystemSyntax
from MooseTextFile import MooseTextFile
from MooseImageFile import MooseImageFile
from MooseInputBlock import MooseInputBlock
from MooseCppMethod import MooseCppMethod
from MoosePackageParser import MoosePackageParser
from MooseSlider import MooseSlider
from MooseDiagram import MooseDiagram
from MooseCSS import MooseCSS
from MooseSlidePreprocessor import MooseSlidePreprocessor
from MooseBuildStatus import MooseBuildStatus
from MooseBibtex import MooseBibtex
import MooseDocs
import utils

class MooseMarkdown(markdown.Extension):
  """
  Extensions that comprise the MOOSE flavored markdown.
  """

  def __init__(self, **kwargs):

    # Storage for the MooseLinkDatabase object
    self.syntax = None

    # Determine the root directory via git
    root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], stderr=subprocess.STDOUT).strip('\n')

    # Define the configuration options
    self.config = dict()
    self.config['root']         = [root, "The root directory of the repository, if not provided the root is found using git."]
    self.config['make']         = [root, "The location of the Makefile responsible for building the application."]
    self.config['executable']   = ['', "The executable to utilize for generating application syntax."]
    self.config['locations']    = [dict(), "The locations to parse for syntax."]
    self.config['repo']         = ['', "The remote repository to create hyperlinks."]
    self.config['links']        = [dict(), "The set of paths for generating input file and source code links to objects."]
    self.config['docs_dir']     = [os.path.basename(os.getcwd()), "The location of the documentation directory, relative to the 'root'"]
    self.config['slides']       = [False, "Enable the parsing for creating reveal.js slides."]
    self.config['package']      = [False, "Enable the use of the MoosePackageParser."]
    self.config['graphviz']     = ['/opt/moose/graphviz/bin', 'The location of graphviz executable for use with diagrams.']
    self.config['dot_ext']      = ['svg', "The graphviz/dot output file extension (default: svg)."]
    self.config['hide']         = [[], "A list of input file syntax to hide from system."]

    # Construct the extension object
    super(MooseMarkdown, self).__init__(**kwargs)

  def execute(self, exe):
    """
    Execute the supplied MOOSE application and return the YAML.

    Args:
      exe[str]: The MOOSE executable.
    """
    if not (exe or os.path.exists(exe)):
      log.error('The executable does not exist: {}'.format(exe))
    else:
      log.debug("Executing {} to extract syntax.".format(exe))
      try:
        raw = utils.runExe(exe, '--yaml')
        return utils.MooseYaml(raw)
      except:
        log.error('Failed to read YAML file, MOOSE and modules are likely not compiled correctly.')
        sys.exit(1);


  def extendMarkdown(self, md, md_globals):
    """
    Builds the extensions for MOOSE flavored markdown.
    """
    md.registerExtension(self)

    # Create a config object
    config = self.getConfigs()

    # Extract YAML
    exe_yaml = self.execute(config.pop('executable', None))

    # Generate YAML data from application
    # Populate the database for input file and children objects
    log.info('Creating input file and source code use database.')
    database = MooseDocs.MooseLinkDatabase(**config)

    # Populate the syntax
    self.syntax = dict()
    for key, value in config['locations'].iteritems():
      if 'hide' in value:
        value['hide'] += config['hide']
      else:
        value['hide'] = config['hide']
      self.syntax[key] = MooseDocs.MooseApplicationSyntax(exe_yaml, **value)

    # Preprocessors
    md.preprocessors.add('moose_bibtex', MooseBibtex(markdown_instance=md, **config), '_end')
    if config['slides']:
      md.preprocessors.add('moose_slides', MooseSlidePreprocessor(markdown_instance=md), '_end')

    # Block processors
    md.parser.blockprocessors.add('diagrams', MooseDiagram(md.parser, **config), '_begin')
    md.parser.blockprocessors.add('slideshow', MooseSlider(md.parser, **config), '_begin')
    md.parser.blockprocessors.add('css', MooseCSS(md.parser, **config), '_begin')

    # Inline Patterns
    object_markdown = MooseObjectSyntax(markdown_instance=md,
                                        yaml=exe_yaml,
                                        syntax=self.syntax,
                                        database=database,
                                        **config)
    md.inlinePatterns.add('moose_object_syntax', object_markdown, '_begin')

    system_markdown = MooseSystemSyntax(markdown_instance=md,
                                        yaml=exe_yaml,
                                        syntax=self.syntax,
                                        **config)
    md.inlinePatterns.add('moose_system_syntax', system_markdown, '_begin')

    md.inlinePatterns.add('moose_input_block', MooseInputBlock(markdown_instance=md, **config), '<image_link')
    md.inlinePatterns.add('moose_cpp_method', MooseCppMethod(markdown_instance=md, **config), '<image_link')
    md.inlinePatterns.add('moose_text', MooseTextFile(markdown_instance=md, **config), '<image_link')
    md.inlinePatterns.add('moose_image', MooseImageFile(markdown_instance=md, **config), '<image_link')
    md.inlinePatterns.add('moose_build_status', MooseBuildStatus(markdown_instance=md, **config), '_begin')
    if config['package']:
      md.inlinePatterns.add('moose_package_parser', MoosePackageParser(markdown_instance=md, **config), '_end')

def makeExtension(*args, **kwargs):
  return MooseMarkdown(*args, **kwargs)
