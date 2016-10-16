#!/usr/bin/python

from nokia import Nokia6100
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
import time
import os.path

# Create an object for the Sparkfun Colour Display
# Define the GPIO pin in use for display reset
nokia = Nokia6100(25)

# Initialise the display. This needs to be called
# once before displaying to the screen
# Display will be on after initialisation
nokia.initialise()

# Open the test image using PIL
img = Image.open('test.jpg')
# Write image to the display.
# This shows in normal orientation for the display. This appears rotated
# when used with the Sparkfun breakout board if the buttons are expected to
# be under the display
nokia.display(img)

# Show the initial display for 2 secs
time.sleep(2)

# Demonstrate the display off and sleep function
nokia.turnOff()
time.sleep(1)

# Turn it back on
nokia.turnOn()

# Orientate the display so the buttons on the Sparkfun board are below
# the screen
nokia.rotate90clockwise()

# Write text to image. This requires freefonts
# If not present then skip this
fntpath = '/usr/share/fonts/truetype/freefont/FreeMono.ttf'
if os.path.isfile(fntpath):
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(fntpath, 15)

    draw.text( (4,img.size[1]/2) , "Orbital Fruit", font=font, fill=(255,255,255))
    nokia.display(img)

    time.sleep(2)

# Do a basic image operation with invert and display
img = ImageOps.invert(img)
nokia.display(img)
