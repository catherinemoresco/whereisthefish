import json
import sys
from config import data_path, image_path
from os.path import abspath, join
from copy import copy
import time

from PIL import Image

__BORDER_WIDTH = 24
__BOX_WIDTH = 135

__json_data = open(abspath(join(data_path, "pokemon.json")))
pokedex_code_map = json.load(__json_data)
__json_data.close()


roster_code_locations = [0xD164, 0xD165, 0xD166, 0xD167, 0xD168, 0xD169]
roster_level_locations = [0xD16E, 0xD19A, 0xD1C6, 0xD1F2, 0xD21E, 0xD24A]
roster_nickname_locations = [(0xD2B5, 0xD2BF), (0xD2C0, 0xD2CA), (0xD2CB, 0xD2D5), (0xD2D6, 0xD2E0), (0xD2E1, 0xD2EB), (0xD2EC, 0xD2F6)]

class Pokemon:
  def __init__(self):
      self.remove()

  def change(self, code, nickname=None):
      try:
          self.name = [''] * 10
          temp_name = list(pokedex_code_map[code]["name"]) if not nickname else list(nickname)
          self.name[0:len(name) - 1] = temp_name[:]
      except:
          self.remove()
      else:
          self.code = code
          self.level = 1

  def remove(self):
      self.name = ['E', 'm', 'p', 't', 'y', '', '', '', '', '']
      self.code = None
      self.level = None

roster = [Pokemon()] * 6

def decode_char(val):
    if val in xrange(0x80, 0x99 + 1):
        return chr(ord('A') + (val - 0x80))
    elif val in xrange(0xA0, 0xB9 + 1):
        return chr(ord('a') + (val - 0xA0))
    else:
        return ''

def monitor_team(pipe):
    global roster
    while True:
        line = pipe.stdout.readline()
        if line == '' and pipe.poll() != None:
            sys.exit()

        # check that lin contains valid address output
        try:
            line = line.rstrip().split(":")
            address = int(line[0], 16)
            val = int(line[1], 16)
        except:
            print "Line format invalid from emulator."
        else:
            if val == 0xff:
                continue
            elif address in roster_code_locations:
                roster[roster_code_locations.index(address)].change(val)
            elif address in roster_level_locations:
                roster[roster_level_locations.index(address)].level = val
            elif address in xrange(roster_nickname_locations[0][0], roster_nickname_locations[-1][-1] + 1):
                full_index = range(roster_nickname_locations[0][0], roster_nickname_locations[-1][-1] + 1).index(address)
                nickname_index = full_index / 11
                char_index = full_index % 11 - 1
                roster[nickname_index].name[char_index] = decode_char(val)

        time.sleep(0)

def render_team(image, draw, font):
    for index, pokemon in enumerate(roster):
        # draw name
        msg = "".join(pokemon.name)
        corner = [__BORDER_WIDTH * (index + 1) + __BOX_WIDTH * index, 490]
        if index > 2:
            corner[0] += 302
        w, h = draw.textsize(msg, font=font)
        centered_corner = copy(corner)
        centered_corner[0] += (__BOX_WIDTH - w) / 2
        draw.text(centered_corner, msg, font=font)

        # draw image
        if pokemon.code != None:
            sprite = Image.open(abspath(join(image_path + "/sprites", pokedex_code_map[pokemon.code]["id"].lstrip("0") + ".png")))
            corner[1] = 549
            w, h = sprite.size
            centered_corner = copy(corner)
            centered_corner[0] += (__BOX_WIDTH - w) / 2
            centered_corner[1] += (__BOX_WIDTH - h) / 2
            image.paste(sprite, tuple(centered_corner))
