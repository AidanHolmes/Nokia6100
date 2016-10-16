# Nokia6100
## What is this?
The nokia.py file contains the Nokia6100 class for use with a Raspberry Pi running Jessie
Noika 6100 displays feature on the [Sparkfun Color LCD Shield](https://www.sparkfun.com/products/retired/9363) for the Arduino, but this display can work with the Raspberry Pi (or any controller with SPI and GPIO). 
There are many examples of this shield being used on the Raspberry Pi with bit banging or creative use of UART. This example uses spidev on the Raspberry Pi by buffering 8bit SPI into 9 byte bursts to the display (allowing for the additional 9th bit for command or data flags).

## How does it work?

PIL does all the hard work managing images and this class accepts a PIL Image to write to the display. 

I do not own the Epson screen, so all code has been tested to work with the Philips PCF8833. I added in code for the Epson S1D15G10D08B000 using information from the "Nokia 6100 LCD Display Driver" revision 1 by James P. Lynch. It may not work as expected or at all.

The code has been lightly tested with Python 2.7 and 3.4. The only incompatibility noted was with the bytes and bytearray types and the code works around this. 

There's an example.py script included with the code which shows how to quickly use the class to open a JPG file and display on the screen.


## Requirements

Python libraries for SPIDEV, PIL (Pillow) and RPi.GPIO

## Class interface

### Class creation Nokia6100(reset, [bus = 0, cs = 0, isepson = 0, mhz = 6])
reset - specify the GPIO pin to use for screen reset. This uses BCM numbering
bus - SPI bus, usually 0 for Raspberry Pi so this is the default
cs - chip select. Either 1 or 0 can be used. BCM pins 8 and 7 are used for 0 and 1 CS when in SPI mode
isepson - set to 1 if using the Epson. Warning, this is totally untested
mhz - specify the speed in MHz. 

### initialise()
Call this before doing anything else. This intialises the display and turns it on.

### close()
Closes the SPI and GPIO. Resets the GPIO which causes the reset line to turn off the display. 
Use this to be tidy and close resources, but this isn't mandatory for GPIO or SPI reuse

### display(image)
Write a PIL image to the display. 
This function will convert to the required format and size if different from 32bit, 132x132.

### turnOn()
Enable the display and wake from a sleep state

### turnOff()
Disable the display and sleep

### rotatenone()
Return the display to default orientation. Hardware connector to top right on the Sparkfun board

### rotate180()
Full rotate the display 180 from default

### rotate90anticlockwise()
Rotate display left 

### rotate90clockwise()
Rotate display right. This is a natural rotation to use the buttons on the Sparkfun shield as the buttons will be along the bottom of the screen.

### printSPI()
Helper function to print the SPI state to standard output.

### other functions
Everthing else is for internal use. writeSPI can be called directly if you want to send some additional commands to the display. Use flushSPI to ensure commands are fully sent. 

