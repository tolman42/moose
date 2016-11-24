from MooseMarkdown import MooseMarkdown
from markdown.util import etree


def full_name(node, action, group_name='.'):

  name = node['name']
  full_name = name.strip('/').split('/')
  if '<type>' in full_name:
    full_name.remove('<type>')
  if '*' in full_name:
    full_name.remove('*')

  if action == 'object':
    full_name.insert(-1, group_name)
    full_name[-1] += '.md'
  elif action == 'system':
    full_name.append('index.md')

  return '/'.join(full_name)


def system_name(node):
  return full_name(node, 'system')


def object_name(node, group_name):
  return full_name(node, 'object', group_name)


def get_collection_items(node, group_name, group_syntax, action):

    items = []

    for child in node['subblocks']:

      name = child['name']
      if name.endswith('*'):
        continue
      short_name = name.split('/')[-1].strip()


      if action == 'object':
          has_items = group_syntax.hasObject(short_name)

      elif action == 'system':
          has_items = group_syntax.hasSystem(name)

      else:
          raise Exception('Unknown value for "action" variable ({}) supplied.'.format(action))


      if has_items:

        item = etree.Element('div')
        item.set('class', 'collection-item')
        items.append(item)

        item_header = etree.SubElement(item, 'div')
        item_header.set('class', 'moose-collection-name')

        #item_desc = etree.SubElement(item, 'div')
        #item_desc.set('class', 'moose-subobjects-description')
        #item_desc.text = child['description']

        a = etree.SubElement(item_header, 'a')
        a.text = short_name
        a.set('href', full_name(child, action, group_name))

    return items


def create_collection(node, syntax, action, groups=[]):
  """
  Creates subobject collection for a given node from the YAML dump.

  Inputs:
    node: The YAML node to inspect.
    syntax: The dict of MooseApplicationSyntax objects
    action[str]: Name of test function on the MooseApplicationSyntax object to call ('system' or 'object')
  """

  groups = groups if groups else syntax.keys()
  use_header = True if len(groups) > 1 else False

  children = []
  for name in groups:
    items = get_collection_items(node, name, syntax[name], action)
    if items and use_header:
      header = etree.Element('div')
      header.set('class', 'collection-header')
      header.text = '{} {}'.format(name.replace('_', ' ').title(), '{}s'.format(action.title()))
      items.insert(0, header)
    children += items

  collection = None
  if children:
    collection = etree.Element('div')
    collection.set('class', 'moose collection with-header')
    collection.extend(children)
  return collection


def create_object_collection(node, syntax, **kwargs):
    return create_collection(node, syntax, 'object', **kwargs)

def create_system_collection(node, syntax, **kwargs):
    return create_collection(node, syntax, 'system', **kwargs)
