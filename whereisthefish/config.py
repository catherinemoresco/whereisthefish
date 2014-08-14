from ConfigParser import ConfigParser
from os.path import abspath, realpath, dirname, join

def __init__(self):
  parser = ConfigParser()
  here = realpath(dirname(__file__))
  parser.read(abspath(join(here, '../config/config.ini')))._sections
  self.config = parser._sections
