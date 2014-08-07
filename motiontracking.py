import cv2
import urllib
import numpy as np
import subprocess
import random
import math

WINDOW_NAME = "Pokemon"
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
  print("fired :" + keycode)
    # subprocess.call(["xdotool", "key", "--window", str(window_id), keycode])

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
  print height/3
  print width/3
  if y < height/3:
    if x < width/3:
      return 0
    if x > 2*width/3:
      return 2
    return 1
  if y > 2*height/3:
    if x < width/3:
      return 6
    if x > 2*width/3:
      return 8
    return 7
  if x < width/3:
    return 3
  if x > 2*width/3:
    return 5
  return 4

def getButtonPress(quadrant):
  return buttons[quadrantButtonMap[quadrant]]["key"], quadrantButtonMap[quadrant]

def assembleOverlay():
  print quadrantButtonMap
  h, w = buttons["B"]["image"].shape[:2]
  overlay = np.zeros((h*3, w*3 + 1, 3), np.uint8)
  overlaymask = np.zeros((h*3, w*3 + 1, 3), np.uint8)
  for quadrant in range(0,9):
    img = buttons[quadrantButtonMap[quadrant]]["image"]
    mask = buttons[quadrantButtonMap[quadrant]]["mask"]

    overlay[h*math.ceil(quadrant/3):h*(math.ceil(quadrant/3) + 1), w*(quadrant % 3):w*(quadrant % 3 + 1)] = img
    overlaymask[h*math.ceil(quadrant/3):h*(math.ceil(quadrant/3) + 1), w*(quadrant % 3):w*(quadrant % 3 + 1)] = mask

  return overlay, overlaymask


height = 480
width = 640
runningAverage = np.zeros((height,width, 3), np.float64) # image to store running avg
stream=urllib.urlopen('***REMOVED***')
bytes=''
areaThreshold = 1000
framecount = 0
# window_id = getWindow()

setQuadrantButtonMap()
overlay, overlayMask = assembleOverlay()

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
        contourImg = np.zeros((height,width, 3), np.uint8)
        cv2.circle(contourImg,(int(ccenter[0]), int(ccenter[1])),3,(0,255,255),2)

        if framecount == 5:
          quadrant = getQuadrant(ccenter)
          print ccenter
          print quadrant
          keycode, value = getButtonPress(quadrant)
          if value == "EMPTY":
            setQuadrantButtonMap()
            overlay, overlayMask = assembleOverlay()
          print(value)
          if keycode != None:
            fire(keycode)
          framecount = 0

        cv2.line(contourImg, (0, height/3), (width, height/3), (255, 255, 255))
        cv2.line(contourImg, (0, 2*height/3), (width, 2*height/3), (255, 255, 255))
        cv2.line(contourImg, (width/3, 0), (width/3, height), (255, 255, 255))
        cv2.line(contourImg, (2*width/3, 0), (2*width/3, height), (255, 255, 255))

        img *= overlayMask
        img += overlay

        cv2.imshow('i', cv2.add(img, contourImg))

        framecount += 1
        if cv2.waitKey(1) ==27:
            exit(0)
