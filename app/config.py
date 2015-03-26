from ConfigParser import SafeConfigParser
from os.path import abspath, realpath, dirname, join
from collections import OrderedDict


here = realpath(dirname(__file__))
asset_path = join(here, '../assets/')
font_path = join(asset_path, 'fonts/')
image_path = join(asset_path, 'images/')
data_path = join(asset_path, 'data/')

def parse_value(value):
  if isinstance(value, (str, unicode)):
    if value.startswith('"') and value.endswith('"'):
      value = value.strip('"')
    elif ',' in value:
      value = [convert_value(part.strip()) for part in value.split(',') if part.strip()]
    elif value.isdigit():
      value = int(value)
    elif FLOAT_PATTERN.match(value):
      value = float(value)
    elif value.lower() == 'true':
      value = True
    elif value.lower() == 'false':
      value = False
  return value

class Section(OrderedDict):
    def __init__(self, data):
      super(Section, self).__init__(
        ((k, parse_value(v)) for k, v in OrderedDict(data).iteritems())
      )

    def __getattr__(self, key):
      if key in self:
        return self[key]
      return object.__getattribute__(self, key)

    def __repr__(self):
      return 'Section(%s)' % dict.__repr__(self)

class Config(OrderedDict):
  def __init__(self):
    parser = SafeConfigParser(dict_type=OrderedDict)
    parser.optionxform = str

    parser.read(abspath(join(here, '../config/config.ini')))

    super(Config, self).__init__(
      (section, Section(parser.items(section))) for section in parser.sections()
    )

  def __getattr__(self, key):
    if key in self:
      return self[key]
    return object.__getattribute__(self, key)

config = Config()
