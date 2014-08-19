from config import config, here
import cv2
import math
import numpy as np
import random
import datetime
import urllib
import subprocess

from os.path import abspath, realpath, join
from screen import Screen
from button import Button
from output import output_stream_pipe

image_path = join(here, '../assets/images/')
overlay_screen = Screen(config.CONTROLLER.WIDTH, config.CONTROLLER.HEIGHT, 3, 3, [
  Button('z', cv2.imread(abspath(join(image_path, "b.png")), 1)),
  Button('x', cv2.imread(abspath(join(image_path, "a.png")), 1)),
  Button('w', cv2.imread(abspath(join(image_path, "up.png")), 1)),
  Button('s', cv2.imread(abspath(join(image_path, "down.png")), 1)),
  Button('a', cv2.imread(abspath(join(image_path, "left.png")), 1)),
  Button('d', cv2.imread(abspath(join(image_path, "right.png")), 1)),
  Button('q', cv2.imread(abspath(join(image_path, "select.png")), 1)),
  Button('e', cv2.imread(abspath(join(image_path, "start.png")), 1)),
  Button(None, cv2.imread(abspath(join(image_path, "empty.png")), 1))
])

def getWindow():
    result = subprocess.check_output(["xdotool", "search","--sync", "--limit", "1", "--name", config.EMULATOR.NAME])
    return result.split("\n")[0]

def diffImg(t1, t2):
    gray1 = cv2.cvtColor(t1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(t2, cv2.COLOR_BGR2GRAY)
    d1 = cv2.absdiff(gray1, gray2)
    blurred = cv2.blur(d1, (15, 15))
    return cv2.threshold(blurred,5,255,cv2.THRESH_BINARY)[1]

def processFrame(bytes):
  a = cv2.imdecode(np.fromstring(bytes, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
  return a

# @TODO: Handle flushing buffers to keep streams synced
# Handle Grayson Stream
stream = urllib.urlopen(config.VIDEO.INPUT)
bytes = ''
framecount = 0
window_id = getWindow()

overlay, overlayMask = overlay_screen.render()

# Handle Output Stream
running_average = np.zeros((config.CONTROLLER.HEIGHT,config.CONTROLLER.WIDTH, 3), np.float64) # image to store running avg
output = np.zeros((config.WINDOW.HEIGHT, config.WINDOW.WIDTH, 3), np.uint8)

keypress_queue = []
while True:
    bytes+=stream.read(1024)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:
        img = processFrame(bytes[a:b+2])
        bytes= bytes[b+2:]

        cv2.accumulateWeighted(img, running_average, .2, None)

        diff = diffImg(img, running_average.astype(np.uint8))

        contours, hierarchy = cv2.findContours(diff, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        contourAreas = {cv2.contourArea(c):c for c in contours}
        if len(contours) != 0:
            maxarea = max(contourAreas.keys())
            if maxarea > config['VIDEO']['AREA_THRESHOLD']:
                largestContour = contourAreas[maxarea]
                ccenter, cradius = cv2.minEnclosingCircle(largestContour)
        contourImg = np.zeros((config.CONTROLLER.HEIGHT,config.CONTROLLER.WIDTH, 3), np.uint8)
        cv2.circle(contourImg,(int(ccenter[0]), int(ccenter[1])),3,(0,255,255),2)

        # Grab Key from Position
        if framecount == 15:
          button = overlay_screen.getButtonFromPosition(ccenter[0], ccenter[1])
          keypress_queue.insert(0, {"image": button.image, "time": datetime.datetime.now().strftime("%H:%M:%S")})
          keypress_queue = keypress_queue[:5]
          if button.keycode == None:
            overlay_screen.shuffle()
            overlay, overlayMask = overlay_screen.render()
          else:
            button.press(window_id)
          framecount = 0

          # append keypresses
          bottombar_bottom_left = (0 , config.WINDOW.HEIGHT)
          to_prepend_width = int(math.floor(config.WINDOW.WIDTH/6))
          cv2.putText(output, "RECENT", (bottombar_bottom_left[0]+50, bottombar_bottom_left[1] - (config.WINDOW.HEIGHT - config.EMULATOR.HEIGHT) + 50), cv2.FONT_HERSHEY_SIMPLEX, .75, (0,200,200), 2)
          cv2.putText(output, "PRESSES", (bottombar_bottom_left[0]+50, bottombar_bottom_left[1] - (config.WINDOW.HEIGHT - config.EMULATOR.HEIGHT) + 100), cv2.FONT_HERSHEY_SIMPLEX, .75, (0,200,200), 2)
          index = 1
          for keypress_object in keypress_queue:
            keypress_img = keypress_object["image"]
            to_prepend = np.resize(keypress_img, (config.WINDOW.HEIGHT - config.EMULATOR.HEIGHT, to_prepend_width, 3))
            cv2.putText(to_prepend, keypress_object["time"], (5, 50), cv2.FONT_HERSHEY_SIMPLEX, .4, (0,200,200), 1)
            output[config.EMULATOR.HEIGHT:, index*to_prepend_width:(index+1)*to_prepend_width] = cv2.cvtColor( to_prepend, cv2.COLOR_BGR2RGB )
            cv2.line(output, (index*to_prepend_width + 1, config.EMULATOR.HEIGHT), (index*to_prepend_width + 1, config.WINDOW.HEIGHT), (255, 255, 255))
            index += 1

        img *= overlayMask
        img += overlay

        controller_frame = cv2.add(img, contourImg)
        controller_frame = overlay_screen.overlayGrid(controller_frame)
        controller_frame = cv2.cvtColor( controller_frame, cv2.COLOR_BGR2RGB )
        output[config.EMULATOR.HEIGHT-config.CONTROLLER.HEIGHT:config.EMULATOR.HEIGHT, config.WINDOW.WIDTH-config.CONTROLLER.WIDTH:config.WINDOW.WIDTH] = controller_frame

        # append time
        time_playing = datetime.datetime.now() - datetime.datetime(2014, 8, 2, 8, 0, 0)
        time_playing_string = '{:02}d {:02}h:{:02}m:{:02}s'.format(time_playing.days, time_playing.seconds // 3600, time_playing.seconds % 3600 // 60, time_playing.seconds % 60)
        topbar_bottom_left = (config.WINDOW.WIDTH-config.EMULATOR.WIDTH , config.EMULATOR.HEIGHT-config.CONTROLLER.HEIGHT)
        output[:topbar_bottom_left[1], topbar_bottom_left[0]:] = np.zeros((topbar_bottom_left[1], topbar_bottom_left[0], 3), np.uint8)
        cv2.putText(output, "Playing For: " + time_playing_string, (topbar_bottom_left[0]+50, topbar_bottom_left[1] - topbar_bottom_left[1]/2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,200,200), 4)

        output_stream_pipe.stdin.write(output.tostring())
        framecount += 1
