import KIP
import osk
import os
import json
from _fbink import ffi, lib as FBInk
from PIL import Image, ImageDraw, ImageFont
import requests
import urllib
from time import sleep

display_width = 1080
input_query = "Integral from 1 to 3 of x**2"  #sample query for test purposes
appid = "AAAAAA-AAAAAAAAAA"
baseURL = "http://api.wolframalpha.com/v1/simple?"
filePath = "result.png"
isKeyboardMode = True
runeStr=""
upperCase = False


def printKeyboard():
	with open('./sample-keymap-en_us.json') as json_file:
		km = json.load(json_file)
		vk = osk.virtKeyboard(km, display_width, 1440)
		# Generate an image of the OSK
		vkPNG = "./osk-en_us.png"
		vk.createIMG(vkPNG)
		# Print the image to the screen. Its position on screen should match that stored
		# in the keyboard object
		FBInk.fbink_print_image(fbfd, vkPNG, int(vk.StartCoords["X"]), int(vk.StartCoords["Y"]), fbink_cfg)
		runeStr = ""
		upperCase = False
		fbink_cfg.row = 0
		fbink_cfg.is_centered = False
		fbink_cfg.is_halfway = False
		return vk

def printHelp():
	fbink_cfg.row=0
	fbink_cfg.col=0
	FBInk.fbink_print(fbfd, "       WOLFRAMALPHA FOR KOBO", fbink_cfg)
	fbink_cfg.row = 2
	FBInk.fbink_print(fbfd, "You can now enter you query", fbink_cfg)
	fbink_cfg.row = 3
	FBInk.fbink_print(fbfd, "Or type 'reboot' to reboot the device", fbink_cfg)
	fbink_cfg.row = 5
	FBInk.fbink_print(fbfd, ">", fbink_cfg)
	fbink_cfg.col = 1


def printWAresult(path):
	fbink_cfg.row=0
	fbink_cfg.col=0
	#Clear screen
	FBInk.fbink_cls(fbfd, fbink_cfg)
	#display_results
	FBInk.fbink_print_image(fbfd, path, 0, 0, fbink_cfg)
	#Display keyboard icon
	FBInk.fbink_print_image(fbfd, "./keyboard_icon.png", 10, 10, fbink_cfg)


def requestWAAPI(input_query,display_width):
	f = { 'appid' : appid, 'i' : input_query,'fontsize' : 30, 'width' : display_width}
	full_query = urllib.urlencode(f)
	full_url = baseURL + str(full_query)
	response = requests.get(full_url)
	if response.status_code == 200:
		with open(filePath, 'wb') as f:
			f.write(response.content)
			return filePath


# INITIALIZING DISPLAY
fbink_cfg = ffi.new("FBInkConfig *")
fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg)
#Clear screen
FBInk.fbink_cls(fbfd, fbink_cfg)

# INITIALIZING TOUCH
touchPath = "/dev/input/event1"
t = KIP.inputObject(touchPath, 1080, 1440)

# INITIALIZING APP
vk = printKeyboard()
printHelp()

while True:
	(x, y,err) = t.getInput()
	if isKeyboardMode:
		if err != None:
			continue
		k = vk.getPressedKey(x, y)
		if k == None :
			continue
		if not k["isKey"]:
			continue
		if k["keyType"] == osk.KTstandardChar:
			if upperCase:
				key = str(k["keyCode"]).upper()
			else:
				key = str(k["keyCode"]).lower()
			runeStr = runeStr + key
			FBInk.fbink_print(fbfd, str(runeStr), fbink_cfg)
		elif k["keyType"] == osk.KTbackspace:
			if len(runeStr) > 0:
				# removing last element and drawing and empty space instead
				runeStr = runeStr[:-1] 
				FBInk.fbink_print(fbfd, str(runeStr) + " ", fbink_cfg)
		elif k["keyType"] == osk.KTcapsLock:
			if upperCase:
				upperCase = False
			else:
				upperCase = True
		elif k["keyType"] == osk.KTcarriageReturn:
			if runeStr == "reboot":
				fbink_cfg.is_centered = True
				fbink_cfg.is_halfway = True
				FBInk.fbink_print(fbfd, "Rebooting...", fbink_cfg)
				os.system("reboot")
			else :
				fbink_cfg.is_centered = True
				fbink_cfg.is_halfway = True
				FBInk.fbink_print(fbfd, "Retrieving result from WolframAlpha...", fbink_cfg)
				fbink_cfg.is_centered = False
				fbink_cfg.is_halfway = False
				requestWAAPI(runeStr,display_width)
				printWAresult(filePath)
				runeStr = ""
				isKeyboardMode = False
		else:
			continue
	else:
		#If outside of the keyboard icon, we ignore
		if x<72 and y<72:
			isKeyboardMode = True
			#Clear screen
			FBInk.fbink_cls(fbfd, fbink_cfg)
			printKeyboard()
			printHelp()