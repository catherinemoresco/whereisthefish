import math
import random

class Screen:
  def __init__(self, height, width, x_grids, y_grids, buttons):
    self.width = width
    self.height = height
    self.x_grid_len = x_grid_len
    self.y_grid_len = y_grid_len
    if len(buttons) > height * width:
      raise ValueError('Attribute, buttons, must the same size as the screen grid')
    self.buttons = buttons
    self.shuffle()

  def shuffle(self):
    self.grid = []
    unused_width = range(self.x_grid_len)
    unused_height = [[x for x in range(self.y_grid_len)] for x in range(self.x_grid_len)]
    for button in self.buttons:
      while True:
        current_x = random.choice(unused_width)
        if len(unused_grid[current_x]) > 0:
          break
      current_y = random.choice(unused_grid[current_x])

      self.grid[current_x][current_y] = button

      unused_height[current_x].remove(current_y)
      if len(unused_height[current_x]) < 1:
        unused_width.remove(current_x)

  def render(self):
    combined_image = np.zeros((self.height, self.width, 3), np.uint8)
    combined_mask = np.zeros((self.height, self.width, 3), np.uint8)

    button_height = math.floor(self.height / self.y_grid_len)
    button_width = math.floor(self.width / self.x_grid_len)

    for x in range(self.x_grid_len):
      for y in range(self.y_grid_len):
        image = np.resize(self.grid[x][y]["image"], (button_height, button_width, 3))
        mask = self.grid[x][y]["mask"]

        combined_image[button_height*y:button_height*(y + 1), button_width*x:button_width*(x + 1)] = image
        combined_mask[button_height*y:button_height*(y + 1), button_width*x:button_width*(x + 1)] = mask

    # Draw Grid Lines
    for x in range(1, self.x_grid_len - 1):
      cv2.line(combined_image, (button_width * x, 0), (button_width * x, self.height), (255, 255, 255))

    for y in range(1, self.y_grid_len - 1):
      cv2.line(combined_image, (0, button_height * y), (self.width, button_height * y), (255, 255, 255))

    return combined_image, combined_mask

  def getButtonFromPosition(self, x, y):
    x_dim = math.floor((self.width / x) * self.x_grid_len)
    y_dim = math.floor((self.height / y) * self.y_grid_len)

    return self.grid[x_dim][y_dim]
