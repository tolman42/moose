import re
import os
import logging
log = logging.getLogger(__name__)

from markdown.util import etree
from MooseSyntaxBase import MooseSyntaxBase
import utils
import MooseDocs

class MooseSystemList(MooseSyntaxBase):
  """
  Creates tables of sub-object/systems.

  !systems
  """

  RE = r'^!systems\s*(.*)'

  def __init__(self, yaml=None, syntax=None, **kwargs):
    MooseSyntaxBase.__init__(self, self.RE, yaml=yaml, syntax=syntax, **kwargs)
    self._settings['title'] = None


  def handleMatch(self, match):
    """
    Handle the regex match.
    """

    groups = self._syntax.keys()

    match.group(2)
    if match.group(2):
      groups = match.group(2).split()
    data = self._yaml.get()


    el = etree.Element('div')
    el.set('class', 'moose-system-list')



    def add_li(items, parent, level=0):

      for item in items:

        name = item['name']
        short_name = name.split('/')[-1].strip()

        if short_name == '<type>':
          continue

        id = short_name.replace(' ', '-').lower()

        div = etree.SubElement(parent, 'div')
        if level == 0:
          div.set('class', 'section scrollspy')
          div.set('id', id)
       # else:
       #   div.set('class', 'moose-system-list-item')

#        header = etree.SubElement(div, 'p')


        h = etree.SubElement(div, 'h{}'.format(str(level+2)))
        h.text = short_name
        h.set('id', id)



        a = etree.SubElement(h, 'a')
        a.set('href', MooseDocs.extensions.system_name(item))
        i = etree.SubElement(a, 'i')
        i.set('class', 'material-icons')
        i.text = 'input'

        if name.endswith('<type>'):
          collection = MooseDocs.extensions.create_object_collection(item, self._syntax, groups=groups)
          if collection:
            div.append(collection)

        elif item['subblocks']:
          if any([child['name'].endswith('*') for child in item['subblocks']]):
            collection = MooseDocs.extensions.create_object_collection(item, self._syntax, groups=groups)
            if collection:
              div.append(collection)
          else:
            add_li(item['subblocks'], etree.SubElement(div, 'div'), level+1)



    add_li(data, el)


    for tag in list(el):
      has_collection = False
      for div in tag.iter('div'):
        if ('class' in div.attrib) and (div.attrib['class'] == 'moose collection with-header'):
          has_collection = True
      if not has_collection:
        el.remove(tag)



    return el
