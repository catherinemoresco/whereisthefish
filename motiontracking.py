import cv2
import urllib
import numpy as np
import subprocess
import random
import math
import datetime

WINDOW_NAME = "Pokemon"
WINDOW_HEIGHT = 720
WINDOW_WIDTH = 1280
FFMPEG_BIN = "ffmpeg"
CONTROLLER_HEIGHT = 480
CONTROLLER_WIDTH = 640
EMULATOR_HEIGHT = 576
EMULATOR_WIDTH = 640
IMG_B = cv2.imread("images/b.png", 1)
IMG_A = cv2.imread("images/a.png", 1)
IMG_UP = cv2.imread("images/up.png", 1)
IMG_DOWN = cv2.imread("images/down.png", 1)
IMG_LEFT = cv2.imread("images/left.png", 1)
IMG_RIGHT = cv2.imread("images/right.png", 1)
IMG_START = cv2.imread("images/start.png", 1)
IMG_SELECT = cv2.imread("images/select.png", 1)
IMG_EMPTY = cv2.imread("images/empty.png", 1)

def getMaskFromOverlay(img):
  overlayMask = cv2.cvtColor( img, cv2.COLOR_BGR2GRAY )
  overlayMask = cv2.threshold( overlayMask, 10, 1, cv2.THRESH_BINARY_INV)[1]
  h,w = overlayMask.shape
  return np.repeat( overlayMask, 3).reshape( (h,w,3) )

buttons = {
  "B": {
    "key": 'z',
    "image": IMG_B,
    "mask": getMaskFromOverlay(IMG_B)
  },
  "A": {
    "key": 'x',
    "image": IMG_A,
    "mask": getMaskFromOverlay(IMG_A)
  },
  "UP": {
    "key": 'w',
    "image": IMG_UP,
    "mask": getMaskFromOverlay(IMG_UP)
  },
  "DOWN": {
    "key": 's',
    "image": IMG_DOWN,
    "mask": getMaskFromOverlay(IMG_DOWN)
  },
  "LEFT": {
    "key": 'a',
    "image": IMG_LEFT,
    "mask": getMaskFromOverlay(IMG_LEFT)
  },
  "RIGHT": {
    "key": 'd',
    "image": IMG_RIGHT,
    "mask": getMaskFromOverlay(IMG_RIGHT)
  },
  "START": {
    "key": 'e',
    "image": IMG_START,
    "mask": getMaskFromOverlay(IMG_START)
  },
  "SELECT": {
    "key": 'q',
    "image": IMG_SELECT,
    "mask": getMaskFromOverlay(IMG_SELECT)
  },
  "EMPTY": {
    "key": None,
    "image": IMG_EMPTY,
    "mask": getMaskFromOverlay(IMG_EMPTY)
  }
}
quadrantButtonMap = {}

def getWindow():
    result = subprocess.check_output(["xdotool", "search", "--name", WINDOW_NAME])
    return result.split("\n")[0]

def fire(keycode):
    subprocess.call(["xdotool", "key", "--window", str(window_id), keycode])

def diffImg(t1, t2):
    gray1 = cv2.cvtColor(t1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(t2, cv2.COLOR_BGR2GRAY)
    d1 = cv2.absdiff(gray1, gray2)
    blurred = cv2.blur(d1, (15, 15))
    return cv2.threshold(blurred,5,255,cv2.THRESH_BINARY)[1]

def processFrame(bytes):
  a = cv2.imdecode(np.fromstring(bytes, dtype=np.uint8),cv2.CV_LOAD_IMAGE_COLOR)
  return a

def setQuadrantButtonMap():
  unused = [0,1,2,3,4,5,6,7,8]
  for key in buttons:
    current = random.choice(unused)
    quadrantButtonMap[current] = key
    unused.remove(current)

def getQuadrant(pos):
  x, y = pos
  if y < CONTROLLER_HEIGHT/3:
    if x < CONTROLLER_WIDTH/3:
      return 0
    if x > 2*CONTROLLER_WIDTH/3:
      return 2
    return 1
  if y > 2*CONTROLLER_HEIGHT/3:
    if x < CONTROLLER_WIDTH/3:
      return 6
    if x > 2*CONTROLLER_WIDTH/3:
      return 8
    return 7
  if x < CONTROLLER_WIDTH/3:
    return 3
  if x > 2*CONTROLLER_WIDTH/3:
    return 5
  return 4

def getButtonPress(quadrant):
  return buttons[quadrantButtonMap[quadrant]]["key"], quadrantButtonMap[quadrant]

def assembleOverlay():
  h, w = buttons["B"]["image"].shape[:2]
  overlay = np.zeros((h*3, w*3 + 1, 3), np.uint8)
  overlaymask = np.zeros((h*3, w*3 + 1, 3), np.uint8)
  for quadrant in range(0,9):
    img = buttons[quadrantButtonMap[quadrant]]["image"]
    mask = buttons[quadrantButtonMap[quadrant]]["mask"]

    overlay[h*math.ceil(quadrant/3):h*(math.ceil(quadrant/3) + 1), w*(quadrant % 3):w*(quadrant % 3 + 1)] = img
    overlaymask[h*math.ceil(quadrant/3):h*(math.ceil(quadrant/3) + 1), w*(quadrant % 3):w*(quadrant % 3 + 1)] = mask

  return overlay, overlaymask

# Handle Grayson Stream
runningAverage = np.zeros((CONTROLLER_HEIGHT,CONTROLLER_WIDTH, 3), np.float64) # image to store running avg
stream=urllib.urlopen(sys.argv[0])
bytes=''
areaThreshold = 1000
framecount = 0
window_id = getWindow()

setQuadrantButtonMap()
overlay, overlayMask = assembleOverlay()

# Handle Emulator Stream
emulator_stream_command = [ FFMPEG_BIN,
            '-f', 'x11grab',
            '-s', str(EMULATOR_WIDTH) + 'x' + str(EMULATOR_HEIGHT),
            '-i', ':0.0',
            '-f', 'image2pipe',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo', '-']
emulator_stream_pipe = subprocess.Popen(emulator_stream_command, stdout = subprocess.PIPE, bufsize=10**8)

# Handle Output Stream
output = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), np.uint8)

command = [ FFMPEG_BIN,
        '-y', # (optional) overwrite output file if it exists
        '-f', 'rawvideo',
        '-vcodec','rawvideo',
        '-s', str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT), # size of one frame
        '-pix_fmt', 'rgb24',
        '-r', '15', # frames per second
        '-i', '-', # The imput comes from a pipe
        '-an', # Tells FFMPEG not to expect any audio
	'-vcodec', 'libx264',
        '-g', '30',
        '-keyint_min', '15',
        '-b', '1000k',
        '-bufsize', '3000k',
	'-minrate', '1000k',
	'-maxrate', '1000k',
        '-pix_fmt', 'yuv420p',
        '-s', str(WINDOW_WIDTH) + 'x' + str(WINDOW_HEIGHT),
	'-preset', 'ultrafast',
	'-tune', 'film',
        '-threads', '2',
        '-strict', 'normal',
        'rtmp://live.twitch.tv/app/' + sys.argv[1] ]

output_stream_pipe = subprocess.Popen( command, stdin=subprocess.PIPE)

keypress_queue = []
while True:
    bytes+=stream.read(1024)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a!=-1 and b!=-1:

        img = processFrame(bytes[a:b+2])
        bytes= bytes[b+2:]

        cv2.accumulateWeighted(img, runningAverage, .2, None)

        diff = diffImg(img, runningAverage.astype(np.uint8))

        contours, hierarchy = cv2.findContours(diff, cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        contourAreas = {cv2.contourArea(c):c for c in contours}
        if len(contours) != 0:
            maxarea = max(contourAreas.keys())
            if maxarea > areaThreshold:
                largestContour = contourAreas[maxarea]
                ccenter, cradius = cv2.minEnclosingCircle(largestContour)
        contourImg = np.zeros((CONTROLLER_HEIGHT,CONTROLLER_WIDTH, 3), np.uint8)
        cv2.circle(contourImg,(int(ccenter[0]), int(ccenter[1])),3,(0,255,255),2)

        if framecount == 5:
          quadrant = getQuadrant(ccenter)
          keycode, value = getButtonPress(quadrant)
          keypress_queue.insert(0, buttons[quadrantButtonMap[quadrant]]["image"])
          keypress_queue = keypress_queue[:5]
          if value == "EMPTY":
            setQuadrantButtonMap()
            overlay, overlayMask = assembleOverlay()
          if keycode != None:
            fire(keycode)
          framecount = 0

        cv2.line(contourImg, (0, CONTROLLER_HEIGHT/3), (CONTROLLER_WIDTH, CONTROLLER_HEIGHT/3), (255, 255, 255))
        cv2.line(contourImg, (0, 2*CONTROLLER_HEIGHT/3), (CONTROLLER_WIDTH, 2*CONTROLLER_HEIGHT/3), (255, 255, 255))
        cv2.line(contourImg, (CONTROLLER_WIDTH/3, 0), (CONTROLLER_WIDTH/3, CONTROLLER_HEIGHT), (255, 255, 255))
        cv2.line(contourImg, (2*CONTROLLER_WIDTH/3, 0), (2*CONTROLLER_WIDTH/3, CONTROLLER_HEIGHT), (255, 255, 255))

        img *= overlayMask
        img += overlay

        controller_frame = cv2.add(img, contourImg)
        controller_frame = cv2.cvtColor( controller_frame, cv2.COLOR_BGR2RGB )

        raw_emulator_image = emulator_stream_pipe.stdout.read(EMULATOR_WIDTH*EMULATOR_HEIGHT*3)
        # transform the byte read into a numpy array
        emulator_image = np.fromstring(raw_emulator_image, dtype='uint8')
        emulator_frame = emulator_image.reshape((EMULATOR_HEIGHT,EMULATOR_WIDTH,3))
        # throw away the data in the pipe's buffer.
        emulator_stream_pipe.stdout.flush()

        output[:EMULATOR_HEIGHT, :EMULATOR_WIDTH] = emulator_frame
        output[EMULATOR_HEIGHT-CONTROLLER_HEIGHT:EMULATOR_HEIGHT, WINDOW_WIDTH-CONTROLLER_WIDTH:WINDOW_WIDTH] = controller_frame
        # append time
        topbar_bottom_left = (WINDOW_WIDTH-EMULATOR_WIDTH , EMULATOR_HEIGHT-CONTROLLER_HEIGHT)
        output[:topbar_bottom_left[1], topbar_bottom_left[0]:] = np.zeros((topbar_bottom_left[1], topbar_bottom_left[0], 3), np.uint8)
        cv2.putText(output, "FPP: " + datetime.datetime.now().strftime("%m-%d-%Y %H:%M:%S-EST"), (topbar_bottom_left[0]+50, topbar_bottom_left[1] - topbar_bottom_left[1]/2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,200,200), 4)

        # append keypresses
        bottombar_bottom_left = (0 , WINDOW_HEIGHT)
        to_prepend_width = int(math.floor(WINDOW_WIDTH/6))
        cv2.putText(output, "RECENT", (bottombar_bottom_left[0]+50, bottombar_bottom_left[1] - (WINDOW_HEIGHT - EMULATOR_HEIGHT) + 50), cv2.FONT_HERSHEY_SIMPLEX, .75, (0,200,200), 2)
        cv2.putText(output, "PRESSES", (bottombar_bottom_left[0]+50, bottombar_bottom_left[1] - (WINDOW_HEIGHT - EMULATOR_HEIGHT) + 100), cv2.FONT_HERSHEY_SIMPLEX, .75, (0,200,200), 2)
        index = 1
        for keypress_img in keypress_queue:
          to_prepend = np.resize(keypress_img, (WINDOW_HEIGHT - EMULATOR_HEIGHT, to_prepend_width, 3))
          cv2.putText(to_prepend, datetime.datetime.now().strftime("%H:%M:%S"), (5, 50), cv2.FONT_HERSHEY_SIMPLEX, .4, (0,200,200), 1)
          output[EMULATOR_HEIGHT:, index*to_prepend_width:(index+1)*to_prepend_width] = cv2.cvtColor( to_prepend, cv2.COLOR_BGR2RGB )
          cv2.line(output, (index*to_prepend_width + 1, EMULATOR_HEIGHT), (index*to_prepend_width + 1, WINDOW_HEIGHT), (255, 255, 255))
          index += 1

        output_stream_pipe.stdin.write(output.tostring())

        framecount += 1
