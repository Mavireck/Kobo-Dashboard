#!/usr/bin/env python
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


#Settings
debounceTime = 200  # minimum time between two clicks (in ms)

# Constants:
KTstandardChar   = 0
KTcarriageReturn = 1
KTbackspace      = 2
KTdelete         = 3
KTcapsLock       = 4
KTcontrol        = 5
KTalt            = 6


def validateKeymap(keyboard):
	# ToDo
	return None


class virtKeyboard:
	"""
	virtual keyboard object 
	"""
	def __init__(self,keymap,fbwidth,fbheight):
		self.keymap = keymap
		self.fbwidth = fbwidth
		self.fbheight = fbheight
		self.prevKey = None
		FBw = float(fbwidth)
		FBh = float(fbheight)
		pxFromTop = int(round(FBh * keymap["kbMargins"]["top"]))
		pxFromBot = int(round(FBh * keymap["kbMargins"]["bottom"]))
		pxFromLeft = int(round(FBw * keymap["kbMargins"]["left"]))
		pxFromRight = int(round(FBw * keymap["kbMargins"]["right"]))
		#Calculate our origin and dimensions from the margins
		self.StartCoords = {}
		self.StartCoords["X"]  =  pxFromLeft
		self.StartCoords["Y"] = pxFromTop
		self.widthPX = fbwidth - pxFromLeft - pxFromRight
		self.heightPX = fbheight - pxFromTop - pxFromBot
		#What's the width of each keymap unit? Rounded down to the nearest pixel of course
		#And the height of each rowheight unit?
		self.kmUnitWidth = int(float(self.widthPX) / keymap["totalKeyWidth"])
		self.rhUnitWidth = int(float(self.heightPX) / keymap["totalRowHeight"])
		self.rows=[]
		self = self.convertKeymap(keymap)
		
	def convertKeymap(self,km):
		currY = self.StartCoords["Y"]
		for r in km["rows"]:
			row={"rowHeight":0,"keys":[]}
			row["rowHeight"] = int(float(self.rhUnitWidth)*r["rowHeight"])
			ky = [{"coord":{}} for j in range(len(r["keys"]))]
			currX = self.StartCoords["X"]
			for j in range(len(r["keys"])):
				ky[j]["width"] = int(float(self.kmUnitWidth) * r["keys"][j]["keyWidth"])
				ky[j]["coord"]["Y"] = currY
				ky[j]["coord"]["X"] = currX
				currX += ky[j]["width"]
				ky[j]["keyType"] = r["keys"][j]["keyType"]
				if r["keys"][j]["isPadding"]:
					ky[j]["isKey"] = False
				else :
					ky[j]["isKey"] = True
				if ky[j]["keyType"] == 0 and len(r["keys"][j]["char"]) > 0:
					# We only care about the first rune...
					ky[j]["keyCode"] = r["keys"][j]["char"][0]
				else:
					ky[j]["keyCode"] = 0
			row["keys"] = ky
			currY += row["rowHeight"]
			self.rows.append(row)
		return self


	def getLabel(self,kt):
		if kt == KTalt:
			return "ALT"
		elif kt == KTbackspace:
			return "BACK"
		elif kt == KTcapsLock:
			return "CAPS"
		elif kt == KTcarriageReturn:
			return "RET"
		elif kt == KTcontrol:
			return "CTRL"
		elif kt == KTdelete:
			return "DEL"
		return ""

	def createIMG(self,savePath):
		white = 255
		black = 0
		gray = 128
		dark_gray = 50

		font_merriweatherRegular = ImageFont.truetype("fonts/Merriweather-Regular.ttf", 30)
		font_merriweatherBold = ImageFont.truetype("fonts/Merriweather-Bold.ttf", 30)

		img = Image.new('L', (self.widthPX, self.heightPX+1), color=white)
		kc = ImageDraw.Draw(img, 'L')
		kc.rectangle([(0,0),(int(self.widthPX),int(self.heightPX+1))],dark_gray)

		for r in self.rows:
			for k in r["keys"]:
				if k["isKey"]:
					kx, ky = int(k["coord"]["X"]-self.StartCoords["X"]), int((k["coord"]["Y"] - self.StartCoords["Y"]))
					kw, kh = int(k["width"]), float(r["rowHeight"])
					kmx, kmy = int(kx + kw/2), int(ky + kh/2)
					kc.rectangle([(kx,ky),(kx+kw,ky+kh)],white,black)
					if k["keyType"] == KTstandardChar:
						kc.text([kmx-15, kmy-15], str(k["keyCode"]).upper(), fill=black, font=font_merriweatherRegular)
					else:
						kc.text([kmx-30, kmy-15], str(self.getLabel(k["keyType"])), fill=black, font=font_merriweatherBold)
		img.save(savePath)
		return savePath


	def getPressedKey(self, inX, inY) :
		""" Given X and Y, we need to find which key was pressed  """
		# First, reject any coordinates that are out of bounds
		if inY < self.StartCoords["Y"] or inY > (self.StartCoords["Y"]+self.heightPX):
			return None
		elif inX < self.StartCoords["X"] or inX > (self.StartCoords["X"]+self.widthPX):
			return None
		# Get the row index.
		rowIndex = -1
		currY = self.StartCoords["Y"]
		i=0
		for r in self.rows :
			if inY <= currY+r["rowHeight"]:
				rowIndex = i
				break
			i += 1
			currY += r["rowHeight"]
		# Getting key in row is a little trickier, as key width varies
		# Linear search, because our list will never be very large...
		if rowIndex >= 0 :
			keyNum = len(self.rows[rowIndex]["keys"])
			for i in range(keyNum):
				k = self.rows[rowIndex]["keys"][i]
				if inX <= (k["coord"]["X"] + k["width"]):
					if k != self.prevKey:
						self.prevKey = k
						self.debounceStartTm= datetime.now()
						return k
					else :
						if  float(timeDelta(self.debounceStartTm,datetime.now())) < debounceTime :
							#print("Debounce detected")
							return None
						else:
							self.prevKey= k
							self.debounceStartTm= datetime.now()
							return k
		print("No matching keys")
		return None



def timeDelta(date1,date2):
	# returns the elapsed milliseconds between the two dates
	dt = date2 - date1
	ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
	return ms