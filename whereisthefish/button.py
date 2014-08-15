import subprocess
import cv2
import numpy as np

class Button:
  def __init__(self, keycode, image):
    self.keycode = keycode
    self.image = image
    self.mask = self.getMaskFromImage(image)

  def press(self, window_id):
    if subprocess.call(["xdotool", "keydown", "--window", str(window_id), self.keycode]) != 0:
        return
    subprocess.call(["sleep", ".1"])
    return subprocess.call(["xdotool", "keyup", "--window", str(window_id), self.keycode])

  # Utility Methods
  @staticmethod
  def getMaskFromImage(image):
    mask = cv2.cvtColor( image, cv2.COLOR_BGR2GRAY )
    mask = cv2.threshold( mask, 10, 1, cv2.THRESH_BINARY_INV)[1]
    h,w = mask.shape
    return np.repeat( mask, 3).reshape( (h,w,3) )
