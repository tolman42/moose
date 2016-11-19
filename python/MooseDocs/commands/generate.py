import os
import MooseDocs
import utils
import logging
log = logging.getLogger(__name__)

def generate_options(parser, subparser):
  """
  Command-line options for generate command.
  """

  generate_parser = subparser.add_parser('generate', help="Check that documentation exists for your application and generate the markdown documentation from MOOSE application executable.")
  generate_parser.add_argument('--disable-stubs', dest='stubs', action='store_false', help="Disable the creation of system and object stub markdown files.")
  generate_parser.add_argument('--locations', nargs='+', help="List of locations to consider, names should match the keys listed in the configuration file.")

  return generate_parser

def generate(config_file='moosedocs.yml', stubs=False, locations=None, **kwargs):
  """
  Generates MOOSE system and object markdown files from the source code.

  Args:
    config_file[str]: (Default: 'moosedocs.yml') The MooseDocs project configuration file.
  """

  # Read the configuration
  config = MooseDocs.load_config(config_file)
  _, ext_config = MooseDocs.get_markdown_extensions(config)
  ext_config = ext_config['MooseDocs.extensions.MooseMarkdown']

  # Run the executable
  exe = MooseDocs.abspath(ext_config['executable'])
  if not os.path.exists(exe):
    raise IOError('The executable does not exist: {}'.format(exe))
  else:
    log.debug("Executing {} to extract syntax.".format(exe))
    raw = utils.runExe(exe, '--yaml')
    yaml = utils.MooseYaml(raw)

  # Populate the syntax
  for key, value in ext_config['locations'].iteritems():
    if (locations == None) or (key in locations):
      syntax = MooseDocs.MooseApplicationSyntax(yaml, name=key, stubs=stubs, **value)
      log.info("Checking documentation for '{}'.".format(key))
      syntax.check()
