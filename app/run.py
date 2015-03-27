from config import config, asset_path, image_path, font_path
import cv2
import math
import numpy as np
import random
import datetime
import urllib
import subprocess
import atexit
import sys
import time
import signal
import shlex

from os.path import abspath, join
from screen import Screen
from button import Button
from pokemon import render_team, monitor_team
from output import output_stream_pipe

from PIL import Image, ImageFont, ImageDraw
from threading import Thread, Timer, Lock

SAVE_BUTTON = Button('F5', 'Save', None, False)
LOAD_BUTTON = Button('F8', 'Load', None, False)
output_frame_string = None

# Handle Process End
def signal_handler(signal, frame):
        print('Terminated, SIGINT caught.')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

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
  a = cv2.resize(a, (config.CONTROLLER.WIDTH, config.CONTROLLER.HEIGHT), interpolation=cv2.cv.CV_INTER_AREA)
  return a

# Start Emulator and begin monitoring current_frame
emulator_pipe = subprocess.Popen([config.EMULATOR.EMULATOR_BIN] + shlex.split(config.EMULATOR.EMULATOR_FLAGS) + [config.EMULATOR.LOCATION], stdout=subprocess.PIPE)
emulator_read_thread = Thread(target=monitor_team, args=(emulator_pipe,))
emulator_read_thread.daemon = True
emulator_read_thread.start()

# get emulator window and load previous save
window_id = getWindow()
LOAD_BUTTON.press(window_id)

def generate_frames():
    global output_frame_string
    global semph
    # Handle Buttons
    overlay_screen = Screen(config.CONTROLLER.WIDTH, config.CONTROLLER.HEIGHT, 3, 3, [
      Button('z', 'B', cv2.imread(abspath(join(image_path, "b.png")), True)),
      Button('x', 'A', cv2.imread(abspath(join(image_path, "a.png")), True)),
      Button('w', 'UP', cv2.imread(abspath(join(image_path, "up.png")), True)),
      Button('s', 'DOWN', cv2.imread(abspath(join(image_path, "down.png")), True)),
      Button('a', 'LEFT', cv2.imread(abspath(join(image_path, "left.png")), True)),
      Button('d', 'RIGH', cv2.imread(abspath(join(image_path, "right.png")), True)),
      Button('q', 'SEL', cv2.imread(abspath(join(image_path, "select.png")), True)),
      Button('e', 'STRT', cv2.imread(abspath(join(image_path, "start.png")), True)),
      Button(None, 'RAND', cv2.imread(abspath(join(image_path, "empty.png")), True))
    ])

    # Handle Grayson Stream
    stream = urllib.urlopen(config.VIDEO.INPUT)
    bytes = ''
    framecount = 0
    savecount = 0

    overlay, overlayMask = overlay_screen.render()

    # Handle Output Stream
    background_frame = Image.open(abspath(join(image_path, "background.png")))
    running_average = np.zeros((config.CONTROLLER.HEIGHT,config.CONTROLLER.WIDTH, 3), np.float64) # image to store running avg
    current_frame = Image.new("RGBA", (config.WINDOW.WIDTH, config.WINDOW.HEIGHT))

    # load fonts
    button_fnt = ImageFont.truetype(abspath(join(font_path, "button.ttf")), size=20)
    label_fnt = ImageFont.truetype(abspath(join(font_path, "label.ttf")), size=11)
    draw = ImageDraw.Draw(current_frame)
    button = None

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

            # Handle Occasional Saving
            if savecount == 1000:
              SAVE_BUTTON.press(window_id)
              savecount = 0
            else:
              savecount += 1

            # Grab Key from Position
            if framecount == 15:
              button = overlay_screen.getButtonFromPosition(ccenter[0], ccenter[1])
              keypress_queue.insert(0, {"image": button.image, "time": datetime.datetime.now().strftime("%H:%M:%S")})
              keypress_queue = keypress_queue[:5]
              if button.keycode == None:
                overlay_screen.shuffle()
                overlay, overlayMask = overlay_screen.render()
              else:
                # press button and render the button that was pressed
                button.press(window_id)

              framecount = 0

            # Add Control overlay to controller stream
            img *= overlayMask
            img += overlay

            # Position Controller
            controller_frame = cv2.add(img, contourImg)
            controller_frame = overlay_screen.overlayGrid(controller_frame)
            controller_frame = cv2.cvtColor(controller_frame, cv2.COLOR_BGR2RGB)
            controller_frame = Image.fromarray(controller_frame)
            current_frame.paste(controller_frame, (652, 24))
            current_frame.paste(background_frame, (0,0), background_frame)

            # append team
            render_team(current_frame, draw, label_fnt)

            # render current button
            if button != None:
                fill_color = 200 / int(math.pow(framecount + 1, 1.5))
                fill = (fill_color,fill_color,fill_color)
                w, h = draw.textsize(button.name, font=button_fnt)
                draw.text((594 + ((92 - w) / 2), 500), button.name, font=button_fnt, fill=fill)
                firstButtonPress = False

            # append time
            time_playing = datetime.datetime.now() - datetime.datetime(2015, 3, 26, 23, 48, 0)
            time_playing_string = '{:02}d{:02}h{:02}m{:02}s'.format(time_playing.days, time_playing.seconds // 3600, time_playing.seconds % 3600 // 60, time_playing.seconds % 60)
            draw.text((24, 703), time_playing_string, font=label_fnt)

            output_frame_string = current_frame.tostring()

            framecount += 1

frame_creation_thread = Thread(target=generate_frames)
frame_creation_thread.daemon = True
frame_creation_thread.start()

lock = Lock()
def pipe_frame():
    lock.acquire()
    t = Timer(0.1, pipe_frame)
    t.daemon = True
    t.start()
    if output_frame_string != None:
        try:
            output_stream_pipe.stdin.write(output_frame_string)
        except IOError:
            t.cancel()
    lock.release()

pipe_frame()

def cleanup():
    timeout_sec = 5
    for p in [emulator_pipe, output_stream_pipe]: # list of your processes
        p_sec = 0
        for second in range(timeout_sec):
            if p.poll() == None:
                time.sleep(1)
                p_sec += 1
            if p_sec >= timeout_sec:
                p.kill() # supported from python 2.6

atexit.register(cleanup)
