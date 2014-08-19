import cv2
import math
import random
import numpy as np

class Screen:
  def __init__(self, width, height, x_grid_len, y_grid_len, buttons):
    self.width = width
    self.height = height
    self.x_grid_len = x_grid_len
    self.y_grid_len = y_grid_len
    if len(buttons) > height * width:
      raise ValueError('Attribute, buttons, must the same size as the screen grid')
    self.buttons = buttons
    self.grid = [[0 for x in range(y_grid_len)] for x in range(x_grid_len)]
    self.button_height = int(math.floor(self.height / self.y_grid_len))
    self.button_width = int(math.floor(self.width / self.x_grid_len))
    self.shuffle()

  def shuffle(self):
    unused_width = range(self.x_grid_len)
    unused_height = [[x for x in range(self.y_grid_len)] for x in range(self.x_grid_len)]
    for button in self.buttons:
      while True:
        current_x = random.choice(unused_width)
        if len(unused_height[current_x]) > 0:
          break
      current_y = random.choice(unused_height[current_x])

      self.grid[current_x][current_y] = button

      unused_height[current_x].remove(current_y)
      if len(unused_height[current_x]) < 1:
        unused_width.remove(current_x)

  def render(self):
    combined_image = np.zeros((self.height, self.width, 3), np.uint8)
    combined_mask = np.zeros((self.height, self.width, 3), np.uint8)

    for x in range(self.x_grid_len):
      for y in range(self.y_grid_len):
        image = np.resize(self.grid[x][y].image, (self.button_height, self.button_width, 3))
        mask = self.grid[x][y].mask

        combined_image[self.button_height*y:self.button_height*(y + 1), self.button_width*x:self.button_width*(x + 1)] = image
        combined_mask[self.button_height*y:self.button_height*(y + 1), self.button_width*x:self.button_width*(x + 1)] = mask

    return combined_image, combined_mask

  def overlayGrid(self, combined_image):
    for x in range(1, self.x_grid_len):
      cv2.line(combined_image, (self.button_width * x, 0), (self.button_width * x, self.height), (255, 255, 255))

    for y in range(1, self.y_grid_len):
      cv2.line(combined_image, (0, self.button_height * y), (self.width, self.button_height * y), (255, 255, 255))

    return combined_image


  def getButtonFromPosition(self, x, y):
    x_dim = int(math.floor((float(x) / float(self.width)) * self.x_grid_len))
    y_dim = int(math.floor((float(y) / float(self.height)) * self.y_grid_len))

    return self.grid[x_dim][y_dim]
