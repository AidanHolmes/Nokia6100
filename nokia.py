# Copyright 2016 Aidan Holmes
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import RPi.GPIO as GPIO
import spidev
import time
from PIL import Image
from sys import version_info

class Nokia6100(object):
        "Nokia 6100 interface for Sparkfun Colour LCD Shield"

        NOKIA_CMD = 0
        NOKIA_DTA = 1

        def __init__(self, reset, cs = 0, isepson = 0, mhz = 6):
                self._reset_pin = reset 
                self._chip_select = cs
                self._width = 132
                self._height = 132
                self._spi = spidev.SpiDev()
                self._curbyte = 0
                self._prevbyte = 0x00
                self._bitbuff = [None] * 9
                self._isepson = isepson
                self._hz = mhz * 1000000

        def writeSPI(self, dc, byte):
                'Write a data or command byte to the buffer'
                out = 0x00

                if self._curbyte == 0:
                        out = (byte >> (self._curbyte+1))
                else:
                        out = (byte >> (self._curbyte+1)) | ((self._prevbyte << (8-self._curbyte)) & 0x00FF)

                if dc == self.NOKIA_CMD:
                        out &= (~(1<<(7-self._curbyte)) & 0x00FF)
                else:
                        out |= (1 << (7-self._curbyte) & 0x00FF)

                self._bitbuff[self._curbyte] = out
                self._prevbyte = byte

                # Fix the last byte and flush out
                if self._curbyte >= 7:
                        # Last byte fits fully into the final 9th byte of buffer
                        self._bitbuff[8] = byte
                        self._spi.xfer2(self._bitbuff)

                        self._prevbyte = 0x00 
                        self._curbyte = 0  # reset counter, just flushed 9 bytes
                else:
                        # Next byte
                        self._curbyte += 1

        def display(self, image):
                'Converts to 12bit colour and resizes. Displays result on hardware screen'
                
                # Display an image from PIL
                # Check the image is correct. Convert and resize if incorrect                
                if image.mode != "RGB":
                        # Convert
                        image = image.convert("RGB")

                if image.size[0] != self._width or image.size[1] != self._height:
                        # Resize
                        image = image.resize((self._width, self._height))
                        
                # Column address set
                if self._isepson:
                        self.writeSPI(self.NOKIA_CMD, 0x15)
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x2A)
                self.writeSPI(self.NOKIA_DTA, 0x00)
                self.writeSPI(self.NOKIA_DTA, self._width - 1)

                # Page address set
                if self._isepson:
                        self.writeSPI(self.NOKIA_CMD, 0x75)
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x2B)
                self.writeSPI(self.NOKIA_DTA, 0x00)
                self.writeSPI(self.NOKIA_DTA, self._height - 1)

                # Write Memory Instruction
                if self._isepson:
                        self.writeSPI(self.NOKIA_CMD, 0x5C)
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x2C)
                
                # Bytes are a different beast in Python 3 and 2
                major_version = version_info[0]
                raw = image.tobytes() # 32 bit RGB
                i = 0
                raw_len = len(raw)
                
                # Write out 12bit colour images from the 32 bit PIL image
                while i < raw_len:
                        btyeout = 0x00
                        if major_version >= 3:
                                byteout = raw[i] & 0xF0
                        else:
                                byteout = ord(raw[i]) & 0xF0
                        i += 1
                        if i < raw_len:
                                if major_version >= 3:
                                        byteout |= (raw[i] >> 4) & 0x0F
                                else:
                                        byteout |= (ord(raw[i]) >> 4) & 0x0F
                                i += 1
                        else:
                                byteout &= 0xF0
                        self.writeSPI(self.NOKIA_DTA, byteout)

                self.flushSPI()
                        
        def flushSPI(self):
                'Write NOOP commands until 9 byte buffer is full and sent to display'
                noop = 0x00 # Philips NOOP
                if self._isepson:
                        noop = 0x25 # Epson NOOP
                # Add rest of bytes as NOOPS. Note Epson and Philips are different
                while self._curbyte > 0:
                        self.writeSPI(self.NOKIA_CMD, noop)

        def close(self):
                'Close GPIO and SPI. Initialise will be needed to open again. This will reset the display'
                # clean up
                GPIO.cleanup()
                self._spi.close()

        def turnOff(self):
                'Turn off the display and put to sleep'
                if self._isepson:
                        self.writeSPI(self.NOKIA_CMD, 0xAE)
                        self.writeSPI(self.NOKIA_CMD, 0x95) # Sleep in
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x28)
                        self.writeSPI(self.NOKIA_CMD, 0x10) # Sleep in
                self.flushSPI()

        def turnOn(self):
                'Wake and turn on the display'
                if self._isepson:
                        self.writeSPI(self.NOKIA_CMD, 0x94)
                        self.writeSPI(self.NOKIA_CMD, 0x20)
                        self.writeSPI(self.NOIKA_DTA, 0x0F)
                        time.sleep(1)
                        self.writeSPI(self.NOKIA_CMD, 0xAF)
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x11)
                        self.writeSPI(self.NOKIA_CMD, 0x03)
                        time.sleep(1)
                        self.writeSPI(self.NOKIA_CMD, 0x29)
                self.flushSPI()
                
        def initialise(self):
                'Initialise the display and open SPI'
                
                self._spi.open(0,0)

                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self._reset_pin, GPIO.OUT)

                # initialise. May need to trigger an edge to set high or low
        
                self._spi.mode = 0
                self._spi.cshigh = False
                self._spi.bits_per_word = 8
                self._spi.max_speed_hz = self._hz
        	
                GPIO.output(self._reset_pin, 0) # Set Low
                time.sleep(2) 
                GPIO.output(self._reset_pin, 1) # Set High
                time.sleep(2)

                if self._isepson:
                        self.initialise_epson()
                else:
                        self.initialise_philips()

                self.flushSPI()

        def initialise_epson(self):
                # Directly copied sequence from James P. Lynch example code
                # Display control. 
                self.writeSPI(self.NOIKA_CMD, 0xCA)
                self.writeSPI(self.NOIKA_DTA, 0x00) # P1: 0x00 = 2 divisions, switching period=8 (default)
                self.writeSPI(self.NOIKA_DTA, 0x20) # P2: 0x20 = nlines/4 - 1 = 132/4 - 1 = 32)
                self.writeSPI(self.NOIKA_DTA, 0x00) # P3: 0x00 = no inversely highlighted lines

                # COM scan
                self.writeSPI(self.NOIKA_CMD, 0xBB)
                self.writeSPI(self.NOIKA_DTA, 0x01) # P1: 0x01 = Scan 1->80, 160<-81

                # Internal oscilator ON
                self.writeSPI(self.NOIKA_CMD, 0xD1)

                # Sleep out
                self.writeSPI(self.NOIKA_CMD, 0x94)

                # Power control
                self.writeSPI(self.NOIKA_CMD, 0x20)
                self.writeSPI(self.NOIKA_DTA, 0x0F) # reference voltage regulator on, circuit voltage follower on, BOOST ON

                # Normal display
                self.writeSPI(self.NOIKA_CMD, 0xA6)

                # Data control
                self.writeSPI(self.NOIKA_CMD, 0xBC)
                self.writeSPI(self.NOIKA_DTA, 0x00) # I'm leaving in normal page addressing (only difference to J P Lynch setup)
                self.writeSPI(self.NOIKA_DTA, 0x00) # P2: 0x00 = RGB sequence (default value)
                self.writeSPI(self.NOIKA_DTA, 0x02) # P3: 0x02 = Grayscale -> 16 (selects 12-bit color, type A)

                # Voltage control (contrast setting)
                self.writeSPI(self.NOIKA_CMD, 0x81)
                self.writeSPI(self.NOIKA_DTA, 32) # P1 = 32 volume value (experiment with this value to get the best contrast)
                self.writeSPI(self.NOIKA_DTA, 3) # P2 = 3 resistance ratio (only value that works)

                time.sleep(1) ;

                # turn on the display
                self.writeSPI(self.NOIKA_CMD, 0xAF)
                
        def initialise_philips(self):
                # SLEEPOUT - turn on booster circuits
                self.writeSPI(self.NOKIA_CMD, 0x11)

                # turn on booster voltage
                self.writeSPI(self.NOKIA_CMD, 0x03)

                # Inversion off
                self.writeSPI(self.NOKIA_CMD, 0x20)

                # Colour pixel format 12 bits
                self.writeSPI(self.NOKIA_CMD, 0x3A)
                self.writeSPI(self.NOKIA_DTA, 0x03)

                # Set up memory access controller.
                self.writeSPI(self.NOKIA_CMD, 0x36)
                self.writeSPI(self.NOKIA_DTA, 0x10)

                # Set contrast
                self.writeSPI(self.NOKIA_CMD, 0x25)
                self.writeSPI(self.NOKIA_DTA, 0x3F)

                time.sleep(2)

                # display on
                self.writeSPI(self.NOKIA_CMD, 0x29)
        
        def rotatenone(self):
                if self._isepson:
                        print("Sorry, not implemented")
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x36)
                        self.writeSPI(self.NOKIA_DTA, 0x10)
                
        def rotate180(self):
                if self._isepson:
                        print("Sorry, not implemented")
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x36)
                        self.writeSPI(self.NOKIA_DTA, 0xC0)

        def rotate90anticlockwise(self):
                if self._isepson:
                        print("Sorry, not implemented")
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x36)
                        self.writeSPI(self.NOKIA_DTA, 0xB0)

        def rotate90clockwise(self):
                if self._isepson:
                        print("Sorry, not implemented")
                else:
                        self.writeSPI(self.NOKIA_CMD, 0x36)
                        self.writeSPI(self.NOKIA_DTA, 0x70)
                
        def printSPI(self):
                'Print to stdout the SPI settings'
                
                print ("Settings:")
                print (" bits_per_word->", self._spi.bits_per_word)
                print (" cshigh->", self._spi.cshigh)
                print (" lsbfirst->", self._spi.lsbfirst)
                print (" max_speed_hz->", self._spi.max_speed_hz)
                print (" mode->", self._spi.mode)





