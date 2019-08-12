#!/usr/bin/env python
"""
KIP : Kobo Input Python

NOTE :
To use this librairy easily, just use:
# touchPath = "/dev/input/event1"
# t = KIP.inputObject(touchPath, 1080, 1440)
Then, you can use a while True loop:
# while True:
#     (x, y, err) = t.getInput()

I can think of 2 ways to implement touch areas:
1/  Keep arrays of length 4 containing x1,y1,x2,y2, the coordinates of the area. 
	Then, for each click, loop through the areas to find the one you clicked on.
	You therefore hardcode which condition apply and which function to execute on click
2/  Define a new class "touchArea([x1,y1,x2,y2],listofVar,functionOnClick)".
	Then you can loop through all instances of the class to find the area you clicked on. 
	You may need to consider looping through a list of global variables 'listOfVar' that must all be True to execute the functionOnClick function.

"""

import os,sys
import struct
import time

evAbs = 3
evKey = 1
evSyn = 0

synReport            = 0
synDropped           = 3
synMTreport          = 2
btnTouch             = 330
absX                 = 0
absY                 = 1
absMTposX            = 53
absMTposY            = 54
absMTPressure        = 58
absMTtouchWidthMajor = 48


touch_path = "/dev/input/event1"
#long int, long int, unsigned short, unsigned short, unsigned int
FORMAT = 'llHHI'
EVENT_SIZE = struct.calcsize(FORMAT)



class inputObject:
	"""
	Input object 
	"""
	def __init__(self,inputPath,vwidth,vheight):
		self.inputPath = inputPath
		self.viewWidth = vwidth
		self.viewHeight = vheight
		self.devFile = open(inputPath, "rb")

	def close(self):
		""" Closes the input event file """
		self.devFile.close()
		return True

	def getEvtPacket(self):
		err = None
		evPacket = []
		badPacket = False
		while True:
			inp_tmp = self.devFile.read(EVENT_SIZE)
			inp = struct.unpack(FORMAT, inp_tmp)
			if not inp:
				print("binary read failed ", inp)
				return None
			(TimeSec,TimeUsec,EvType,EvCode,EvValue) = inp
			if EvType ==evSyn and EvCode == synDropped:
				# we need to ignore all packets up to, and including the next
				# SYN_REPORT
				badPacket=True
				evPacket=None
				continue
			if badPacket and EvType ==evSyn and EvCode == synReport:
				# We encountered a SYN_DROPPED previously. Return with an error
				print("Error : bad event packet")
				return None
			if not badPacket:
				evPacket.append(inp)
				if EvType == evSyn and EvCode == synReport:
					# We have a complete event packet
					return evPacket


	def getInput(self):
		"""
		Returns the rotated x,y coordinates of where the user touches
		"""
		err = None
		x,y=-1,-1
		touchPressed=False
		touchReleased=False
		getEvAttempts=0
		decodeEvAttempts=0
		while True:
			evPacket = self.getEvtPacket()
			if not evPacket:
				#We have to try again, increasing the attempts counter
				getEvAttempts += 1
				continue
			if getEvAttempts > 4:
				err = 1
				#print("oups error line 101 of KIP")
				return err
			#if we have got this far, we can reset the counter
			getEvAttempts = 0
			#Now to decode :
			for e in evPacket:
				if e[2] == evKey:
					if e[3] == bntTouch:
						if e[4] == 1:
							touchPressed = True
						else :
							touchReleased = True
				elif e[2] == evAbs:
					if e[3] == absX:
						x=int(e[4])
					elif e[3] == absY:
						y=int(e[4])
					elif e[3] == absMTposX:
						x=int(e[4])
					elif e[3] == absMTposY:
						y=int(e[4])
					# Some kobo's seem to prefer using pressure to detect touch pressed/released
					elif e[3] == absMTPressure:
						if e[4] >0 :
							touchPressed = True
						else:
							touchReleased = True
					# And others use the ABS_MT_WIDTH_MAJOR (and ABS_MT_TOUCH_MAJOR too, but those
					# are also used and set to zero on other kobo versions) instead :(
					elif e[3] == absMTtouchWidthMajor:
						if e[4] > 0:
							touchPressed = True
						else :
							touchReleased = True
			# We've decoded one packet. Do we need to continue?
			if x >= 0 and y >= 0 and touchPressed and touchReleased:
				# No, we have all the information we need
				#print("nah we have all we need")
				break

			# To ensure we never get caught in an infinite loop
			if decodeEvAttempts < 5 :
				decodeEvAttempts += 1
			else : 
				x, y = -1, -1
				err = "unable to decode complete touch packet"
				print(err)
				return (x, y, err)
		"""
			Coordinate rotation needs to happen.
			For reference, from FBInk, a clockwise rotation is as follows:
			rx = y
			ry = width - x - 1
			But we need to rotate counter-clockwise...
		"""
		ry = x
		rx = self.viewWidth - y + 1
		#print("Results returned")
		return (rx, ry, None)
