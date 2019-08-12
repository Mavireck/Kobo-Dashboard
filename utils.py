#!/usr/bin/env python

import sys
import os
# Load the wrapper module, it's linked against FBInk, so the dynamic loader will take care of pulling in the actual FBInk library
from _fbink import ffi, lib as fbink
# Load keyboard librairy
import osk
import json
# Load Pillow
from PIL import Image, ImageDraw, ImageFont
# Load touch librairy
import KIP
# Load Time (for debounce purposes)
from time import time

# Setup
pp_color = 240
pp_outline = 50
white = 255
black = 0
gray = 128
default_screenWidth = 1080
default_screenHeight = 1440
touchPath = "/dev/input/event1"
small_font = ImageFont.truetype("fonts/Merriweather-Regular.ttf", 26)
small_font_bold = ImageFont.truetype("fonts/Merriweather-Bold.ttf", 26)





def mfullscreen_refresh():
	try:
		os.system("fbink -refresh") #Was not able to do it through the Python API (a few errors come in)
		return True
	except:
		return False

def mprint(string,row=0,col=0):
	fbink_cfg.row = row
	fbink_cfg.col = col
	fbink.fbink_print(fbfd, string, fbink_cfg)
	fbink_cfg.row = 0
	fbink_cfg.col = 0
	return True

def mpopup(title, text,buttons,filePath="temp_mpopup.png",screen_width=default_screenWidth,screen_height=default_screenHeight):
	"""
	Pauses the app, displays a popup with as many buttons as there are in the array 'button'
	Then restore a screen dump from before the popup appeared
	Then returns the button which was pressed
	"text", "title" and button's "text" may contain eof characters (untested)
	Usage for a yes/no question:
	import utils
	buttons = [{"text":"Yes","valueToReturn":True},{"text":"No","valueToReturn":False}]
	doesUserLikeCheese = utils.mpopup("Cheese","Do you like cheese?",buttons)
	"""
	# Setup the config...
	fbink_cfg = ffi.new("FBInkConfig *")
	# Open the FB...
	fbfd = fbink.fbink_open()
	fbink.fbink_init(fbfd, fbink_cfg)
	# INITIALIZING TOUCH
	t = KIP.inputObject(touchPath, screen_width,screen_height)
	# Init :
	pp_width = int(3*screen_width/5)
	pp_height = int(screen_height/3)
	start_coord_x = int(1*screen_width/5)
	start_coord_y = int(1*screen_width/3)
	num_btns = len(buttons)
	img = Image.new('L', (pp_width+1,pp_height+1), color=white)
	mpopup_img = ImageDraw.Draw(img, 'L')
	# Main rectangle:
	mpopup_img.rectangle([(0,0),(pp_width,pp_height)],fill=pp_color,outline=pp_outline)
	# Main separation lines:
	mpopup_img.line([0,int(pp_height/4),pp_width,int(pp_height/4)], pp_outline) # Title and text
	mpopup_img.line([0,int(3*pp_height/4),pp_width,int(3*pp_height/4)], pp_outline) # text and buttons
	# Main texts
	title_w,title_h = mpopup_img.textsize(title, font=small_font_bold)
	mpopup_img.text((int(pp_width/2-0.5*title_w),int(pp_height/8-0.5*title_h)), title, font=small_font_bold, fill=black)
	text_w,text_h = mpopup_img.textsize(text, font=small_font)
	mpopup_img.text((int(pp_width/2-0.5*text_w),int(pp_height/2-0.5*text_h)), text, font=small_font, fill=black)
	# Separation between buttons and buttons text :
	btns_areas = []
	for i in range(num_btns):
		btn_area=[int((i)*pp_width/num_btns),int(3*pp_height/4),int((i+1)*pp_width/num_btns),pp_height]
		btns_areas.append(btn_area)
		mpopup_img.rectangle(btn_area, fill=white,outline=pp_outline)
		btn_w,btn_h = mpopup_img.textsize(buttons[i]["text"], font=small_font)
		mpopup_img.text((int((btn_area[0]+btn_area[2])/2-0.5*btn_w),int(3*pp_height/4+pp_height/8-0.5*btn_h)), buttons[i]["text"], font=small_font, fill=black)
	# Saving to a file :
	img.save(filePath)
	# Making a copy of the screen
	fbink_dumpcfg = ffi.new("FBInkDump *")
	fbink.fbink_region_dump(fbfd,start_coord_x, start_coord_y,start_coord_x+pp_width+1,start_coord_y+pp_height+1,fbink_cfg,fbink_dumpcfg)
	# Displaying image
	fbink.fbink_print_image(fbfd, filePath, start_coord_x, start_coord_y, fbink_cfg)
	# Listening for touch in one of a button's area
	lastTouch=time()
	while True:
		try:
			(x, y, err) = t.getInput()
			if time()-lastTouch>0.2:
				lastTouch=time()
				relative_x=x-start_coord_x
				relative_y=y-start_coord_y
				for i in range(num_btns):
					if coordsInArea(relative_x,relative_y,btns_areas[i]):
						#Closing touch file
						t.close()
						#Restoring dump
						fbink.fbink_restore(fbfd,fbink_cfg,fbink_dumpcfg)
						fbink.fbink_close(fbfd)
						#Returning value
						return buttons[i]["valueToReturn"]
		except:
			print("Bad touch event")
			continue

def mprompt(title, text,filePath="temp_mprompt.png",screen_width=default_screenWidth,screen_height=default_screenHeight):
	"""
	Pauses the app, displays a popup with an on-screen-keyboard
	Then restore a screen dump from before the popup appeared
	Then returns the string)
	"""
	# Setup the config...
	fbink_cfg = ffi.new("FBInkConfig *")
	# Open the FB...
	fbfd = fbink.fbink_open()
	fbink.fbink_init(fbfd, fbink_cfg)
	# INITIALIZING TOUCH
	t = KIP.inputObject(touchPath, screen_width,screen_height)
	# INITIALIZING KEYBOARD
	with open('sample-keymap-en_us.json') as json_file:
		km = json.load(json_file)
		vk = osk.virtKeyboard(km, screen_width, screen_height)
		# Generate an image of the OSK
		vkPNG = "img/vk.png"
		vk.createIMG(vkPNG)
	# Init :
	pp_width = int(4*screen_width/5)
	pp_height = int(screen_height/3)
	start_coord_x = int(0.5*screen_width/5)
	start_coord_y = int(1*screen_width/3)
	img = Image.new('L', (pp_width+1,pp_height+1), color=white)
	mpopup_img = ImageDraw.Draw(img, 'L')
	# Main rectangle:
	mpopup_img.rectangle([(0,0),(pp_width,pp_height)],fill=pp_color,outline=pp_outline)
	# Main separation lines:
	mpopup_img.line([0,int(pp_height/4),pp_width,int(pp_height/4)], pp_outline) # Title and text
	mpopup_img.line([0,int(3.2*pp_height/4),pp_width,int(3.2*pp_height/4)], pp_outline) # text and buttons
	# Main texts
	title_w,title_h = mpopup_img.textsize(title, font=small_font_bold)
	mpopup_img.text((int(pp_width/2-0.5*title_w),int(pp_height/8-0.5*title_h)), title, font=small_font_bold, fill=black)
	text_w,text_h = mpopup_img.textsize(text, font=small_font)
	mpopup_img.text((int(pp_width/2-0.5*text_w),int(pp_height/2-0.5*text_h)), text, font=small_font, fill=black)
	# Saving to a file :
	img.save(filePath)
	# Making a copy of the screen
	fbink_dumpcfg = ffi.new("FBInkDump *")
	fbink.fbink_region_dump(fbfd,0, 0,screen_width,screen_height,fbink_cfg,fbink_dumpcfg)
	# Displaying image of the popup
	fbink.fbink_print_image(fbfd, filePath, start_coord_x, start_coord_y, fbink_cfg)
	# Displaying image of the OSK
	fbink.fbink_print_image(fbfd,vkPNG, int(vk.StartCoords["X"]), int(vk.StartCoords["Y"]),fbink_cfg)
	# Listening for touch in one of a button's area
	lastTouch=time()
	lastTouchArea=[-3,-3,-2,-2]
	runeStr=""
	upperCase=False
	# For an easy example, we only print it "manually" at the correct place. 
	# You may want to print it using a better font and at a fixed coordinates 
	# Should you want it, the text should be printed at the following coordinates:
	# x  =  start_coord_x + int(3.2*pp_height/4) + 10
	# y  =  start_coord_y + 10
	fbink_cfg.row=32
	fbink_cfg.col=6
	while True:
		try:
			(x, y, err) = t.getInput()
			if time()-lastTouch>0.2 or not coordsInArea(x,y,lastTouchArea):
				# Simple yet effective debounce system
				lastTouchArea=[x-7,y-7,x+7,y+7]
				k = vk.getPressedKey(x, y)
				if k != None:
					if not k["isKey"]:
						continue
					if k["keyType"] == osk.KTstandardChar:
						if upperCase:
							key = str(k["keyCode"]).upper()
						else:
							key = str(k["keyCode"]).lower()
						runeStr = runeStr + key
						fbink.fbink_print(fbfd, str(runeStr), fbink_cfg)
					elif k["keyType"] == osk.KTbackspace:
						if len(runeStr) > 0:
							# removing last element and drawing and empty space instead
							runeStr = runeStr[:-1] 
							fbink.fbink_print(fbfd, str(runeStr) + " ", fbink_cfg)
					elif k["keyType"] == osk.KTcapsLock:
						if upperCase:
							upperCase = False
						else:
							upperCase = True
					elif k["keyType"] == osk.KTcarriageReturn:
						#Closing touch file
						t.close()
						#Restoring dump
						fbink.fbink_restore(fbfd,fbink_cfg,fbink_dumpcfg)
						fbink.fbink_close(fbfd)
						return runeStr
					else:
						continue
		except:
			print("Bad touch event")
			continue
	return True


def coordsInArea(x,y,area):
	if x>=area[0] and x<area[2] and y>=area[1] and y<area[3]:
		return True
	else:
		return False
