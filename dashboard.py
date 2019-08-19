# -*- coding:utf-8 -*-
# System and threading
import os
import sys
import socket
import threading
import multiprocessing
import time
import locale
# Tools
import json
import requests
import math
from base64 import b64decode
import ctypes
# FBInk and Pillow
from _fbink import ffi, lib as FBInk
from PIL import Image, ImageDraw, ImageFont
import PIL.ImageOps
# My own librairies (Kobo-Input-Python, Kobo-Python-OSKandUtils)
sys.path.append('../Kobo-Input-Python')
sys.path.append('../Kobo-Python-OSKandUtils')
import KIP
import osk

# Now for the Python-version-dependent modules:
try:
	from SimpleHTTPServer import SimpleHTTPRequestHandler
except ImportError:
	from http.server import SimpleHTTPRequestHandler
try:
	from SocketServer import TCPServer as HTTPServer
except ImportError:
	from http.server import HTTPServer
try:
	from urlparse import parse_qs
except ImportError:
	from urllib.parse import urljoin


###############################################################################################
"""
# TODO:
TO DO : Keep the last file and a variable called "last_update_XXX".
If the device goes offline, it can still display the last version it received.
"""
###############################################################################################
###############################################################################################
# READ CONFIG FILE
with open('files/config.json') as json_file:
	conf = json.load(json_file)


# INITIALIZING DISPLAY
fbink_cfg_clock = ffi.new("FBInkConfig *")
fbink_cfg_weather = ffi.new("FBInkConfig *")
fbink_cfg = ffi.new("FBInkConfig *")
fbink_cfg_notification = ffi.new("FBInkConfig *")
fbink_cfg_quotes = ffi.new("FBInkConfig *")
fbink_cfg_IP = ffi.new("FBInkConfig *")
fbink_dumpcfg = ffi.new("FBInkDump *")
fbfd = FBInk.fbink_open()
FBInk.fbink_init(fbfd, fbink_cfg_IP)

fbink_ot_cfg = ffi.new("FBInkOTConfig *")
FBInk.fbink_add_ot_font("fonts/Merriweather-Regular.ttf", FBInk.FNT_REGULAR);
FBInk.fbink_add_ot_font("fonts/Merriweather-RegularItalic.ttf", FBInk.FNT_ITALIC);
FBInk.fbink_add_ot_font("fonts/Merriweather-BoldItalic.ttf", FBInk.FNT_BOLD_ITALIC);
FBInk.fbink_add_ot_font("fonts/Merriweather-Bold.ttf", FBInk.FNT_BOLD);

#Get screen infos
state = ffi.new("FBInkState *")
FBInk.fbink_get_state(fbink_cfg, state)
screen_width=state.screen_width
screen_height=state.screen_height

#Clear screen
FBInk.fbink_cls(fbfd, fbink_cfg_IP)

###############################################################################################

sleep_quote = 60*60*4	# every 4 hours or on touch
sleep_gkeep = 60*30  	# every 30 minutes or on touch
updateWeatherAt = 7

last_update_weather = 0
last_update_notification = 0
last_update_calendar = 0

keyboardCallFunction=False
isKeyboardMode = False
border = 10
useOldPrintImg = False

isNightMode=conf["main"]["general"]["isNightMode"]
frontlightLevel = 0

tiny_tiny_tiny_font = ImageFont.truetype("fonts/Cabin-Regular.ttf", 15)
tiny_tiny_font = ImageFont.truetype("fonts/Cabin-Regular.ttf", 18)
tiny_font = ImageFont.truetype("fonts/Cabin-Regular.ttf", 24)
small_font = ImageFont.truetype("fonts/Merriweather-Regular.ttf", 26)
small_font_bold = ImageFont.truetype("fonts/Merriweather-Bold.ttf", 26)
font = ImageFont.truetype("fonts/Forum-Regular.ttf", 50)
comfortaa_big = ImageFont.truetype("fonts/Comfortaa-Regular.ttf", 180)
comfortaa = ImageFont.truetype("fonts/Comfortaa-Regular.ttf", 80)
comfortaa_small = ImageFont.truetype("fonts/Comfortaa-Regular.ttf", 40)

white = 255
black = 0
gray = 128

clock_area = [0,0,screen_width,int(screen_height*conf["main"]["clock"]["size"])]
calendar_area = [0,clock_area[3],screen_width,clock_area[3]+int(screen_height*conf["main"]["calendar"]["size"])]
weather_area = [0,calendar_area[3],screen_width,calendar_area[3]+int(screen_height*conf["main"]["weather"]["size"])]
notification_area = [0,weather_area[3],screen_width,weather_area[3]+int(screen_height*conf["main"]["notif"]["size"])]


# Relative position within the weather area :
weather_area_today = [0,0,int(0.66*weather_area[2]),weather_area[3]-weather_area[1]]
weather_area_coming_days = [weather_area_today[2]+1,0,weather_area[2],weather_area[3]-weather_area[1]]
weather_area_coming_day_1 = [weather_area_coming_days[0],weather_area_coming_days[1],weather_area_coming_days[2],weather_area_coming_days[1]+int(0.33*(weather_area_coming_days[3]-weather_area_coming_days[1]))]
weather_area_coming_day_2 = [weather_area_coming_days[0],weather_area_coming_day_1[3],weather_area_coming_days[2],weather_area_coming_day_1[3]+int(0.33*(weather_area_coming_days[3]-weather_area_coming_days[1]))]
weather_area_coming_day_3 = [weather_area_coming_days[0],weather_area_coming_day_2[3],weather_area_coming_days[2],weather_area_coming_day_2[3]+int(0.33*(weather_area_coming_days[3]-weather_area_coming_days[1]))]
weather_area_t6 = [weather_area_today[0],weather_area_today[1]+40,int(1*weather_area_today[2]/6),weather_area_today[3]]
weather_area_t9 = [weather_area_t6[2],weather_area_today[1]+40,int(2*weather_area_today[2]/6),weather_area_today[3]]
weather_area_t12 = [weather_area_t9[2],weather_area_today[1]+40,int(3*weather_area_today[2]/6),weather_area_today[3]]
weather_area_t15 = [weather_area_t12[2],weather_area_today[1]+40,int(4*weather_area_today[2]/6),weather_area_today[3]]
weather_area_t18 = [weather_area_t15[2],weather_area_today[1]+40,int(5*weather_area_today[2]/6),weather_area_today[3]]
weather_area_t21 = [weather_area_t18[2],weather_area_today[1]+40,int(6*weather_area_today[2]/6),weather_area_today[3]]

#Relative position within the calendar area:
calendar_area_days = [[calendar_area[0]+int(i*(calendar_area[2]-calendar_area[0])/conf["main"]["calendar"]["numberOfDaysOnScreen"]),0,calendar_area[0]+int((i+1)*(calendar_area[2]-calendar_area[0])/conf["main"]["calendar"]["numberOfDaysOnScreen"]),calendar_area[3]-calendar_area[1]] for i in range(conf["main"]["calendar"]["numberOfDaysOnScreen"])]
calendar_area_addEvent_Textboxes_area=[]  	#Global variable initialization (they will be properly defined later)
calendar_area_addEvent_beginHour=[]
calendar_area_addEvent_endHour=[]
calendar_area_addEvent_Title=[]
calendar_area_addEvent_Color=[]
calendar_area_addEvent_Save=[]
calendar_area_addEvent_Back=[]
calendar_area_addEvent_Delete=[]
day_h_sample_calendar = 32  # Defined properly in printCalendar_singleDay()
calendar_area_weekView_weekChange_Back=[calendar_area_days[0][0],calendar_area_days[0][1],calendar_area_days[0][2],calendar_area_days[0][1]+2*border+day_h_sample_calendar]
calendar_area_weekView_weekChange_Forward=[calendar_area_days[-1][0],calendar_area_days[-1][1],calendar_area_days[-1][2],calendar_area_days[-1][1]+2*border+day_h_sample_calendar]

#Relative position within the clock area:
clock_area_wifiBtn=[]
clock_area_rebootBtn=[]
clock_area_frontlightBtnUP=[]
clock_area_frontlightBtnDOWN=[]
clock_area_invertBtn=[]



###############################################################################################
notifications_history = []
log_history = []
displayMode = "Notifications"

httpd = None
class S(SimpleHTTPRequestHandler):
	def _set_headers(self):
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

	def do_POST(self):
		try:
			# Doesn't do anything with posted data
			content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
			post_data = self.rfile.read(content_length) # <--- Gets the data itself
			# Now convert to dictionary :
			post_data = parse_qs(post_data)
			decoded_data = {val:dataDecoder(post_data,val) for val in post_data}
			global notifications_history
			notifications_history.append(decoded_data)
			notifications_history = cleanDuplicate(notifications_history)
			displayArray(notifications_history,"Notifications")
			self._set_headers()
			self.wfile.write("<html><body><h1>DONE!</h1><pre></pre></body></html>")
		except:
			mprintLog("Notification module has crashed")
			mprintLog(str(sys.exc_info()[0]))
			mprintLog(str(sys.exc_info()[1]))
			return False

def run(server_class=HTTPServer, handler_class=S, port=80):
	global httpd
	try:
		server_address = ('', port)
		httpd = server_class(server_address, handler_class)
		print('Starting httpd...')
		httpd.serve_forever()
	except:
		try:
			httpd.shutdown()
			print('httpd killed')
		except:
			print('Error starting httpd. Instance already running ?')
			print('Module "notification" crashed. Continuing.')
			return True

def dataDecoder(dicti,val):
	try:
		r=b64decode(dicti[val][0])
		return r
	except:
		print(dicti)
		print(val)
		print(dicti[val])
		if val=="timestamp":
			return dicti[val][0]
		else:
			return ""

def displayArray(arrayToDisplay,mode):
	global notifications_history
	global log_history
	global displayMode
	displayMode = mode
	img = Image.new('L', (notification_area[2]-notification_area[0], notification_area[3]-notification_area[1]-1), color=white)
	notifsImg = ImageDraw.Draw(img, 'L')
	# Displaying mode
	mode_w, mode_h = notifsImg.textsize(mode, font=small_font)
	notifsImg.text((int(0.5*(notification_area[2]+notification_area[0])-0.5*mode_w),10), mode, font=small_font, fill=black)
	# Popping element if there are too many
	sample_notif_title_w, sample_notif_title_h = notifsImg.textsize("- AVERAGE2 height of the texts |", font=tiny_font)
	while len(arrayToDisplay)*sample_notif_title_h+mode_h+20>notification_area[3]-notification_area[1]:
		arrayToDisplay = arrayToDisplay[1:]
		if mode == "Notifications":
			notifications_histoy=arrayToDisplay
		else:
			log_history = arrayToDisplay
	# Displaying every notification
	start_h_offset_notif = 10+mode_h
	for notif in arrayToDisplay:
		try:
			date = time.strftime("%H:%M", time.localtime(int(float(notif["timestamp"]))))
		except:
			#One can also assume the date is time.time() instead of an empty string
			date = ""
		try:
			temp_title_notif = str(notif["title"])[:conf["main"]["notif"]["title_maxLength"]].decode('utf-8')
		except:
			temp_title_notif = str(notif["title"])[:conf["main"]["notif"]["title_maxLength"]]
		notif_title_w, notif_title_h = notifsImg.textsize(temp_title_notif, font=tiny_font)
		if temp_title_notif == "":
			notif_title_w_gne, notif_title_h = notifsImg.textsize("Sample", font=tiny_font)
		try:
			temp_text_notif = " - " + notif["message"].decode('utf-8')[:conf["main"]["notif"]["total_maxLength"]-len(temp_title_notif)] + " | " + notif["package"].decode('utf-8') + " " + str(date).decode('utf-8')
		except:
			temp_text_notif = " - " + notif["message"][:conf["main"]["notif"]["total_maxLength"]-len(temp_title_notif)] + " | " + notif["package"] + " " + str(date)
		# temp_text_notif = " - " + notif[0]["message"] + " | "  + " @ " + str(date)
		notifsImg.text((10,start_h_offset_notif), temp_title_notif, font=tiny_font, fill=black)
		notifsImg.text((10+notif_title_w,start_h_offset_notif), temp_text_notif, font=tiny_font, fill=black)
		start_h_offset_notif += notif_title_h + 8
	img.save(conf["imgPath"]["notifications"])
	if useOldPrintImg:
		# OLD WAY
		mprintImg_path(conf["imgPath"]["notifications"], notification_area[0], notification_area[1]+1)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,notification_area[0], notification_area[1]+1,img.width,img.height,raw_len)
	return True

def cleanDuplicate(arrayToClean):
	"""
	Sometimes, the device sends multiple times the exact same notification.
	We clean the duplicates.
	"""
	cleanedArray = []
	for i in arrayToClean:
		if i not in cleanedArray:
			cleanedArray.append(i)
	return cleanedArray

def mprintLog(logText):
	global log_history
	print(str(logText))
	lg = {"message":str(logText),"title":"","package":"","timestamp":""}
	log_history.append(lg)
	displayArray(log_history,"Log")

def onTouchNotification(x,y):
	global notifications_history
	global log_history
	global displayMode
	if displayMode == "Notifications":
		displayArray(log_history,"Log")
	else:
		displayArray(notifications_history,"Notifications")
	return True

###############################################################################################
def setupClock():
	mprintLog("Clock Launched")
	printClock(time.time())
	next_minute = math.ceil(int(time.time())/60)*60 +60
	# We wait for the next minute
	time.sleep(int(next_minute)-int(time.time())+1)
	# Then we start it so that it updates every minute (or every given time)
	while True :
		printClock(time.time())
		time.sleep(conf["main"]["clock"]["sleep"])

def printClock(time_arg):
	global clock_area_wifiBtn
	global clock_area_rebootBtn
	global clock_area_frontlightBtnUP
	global clock_area_frontlightBtnDOWN
	global clock_area_invertBtn
	global frontlightLevel
	global isWifiOn
	clockToDisplay = time.strftime("%H:%M", time.localtime(time_arg))
	dateToDisplay = time.strftime("%A %d %B %Y", time.localtime(time_arg))
	img = Image.new('L', (clock_area[2], clock_area[3]), color=white)
	clock = ImageDraw.Draw(img, 'L')
	# Draw IP in the top right corner
	ip_address=get_ip()
	ip_w, ip_h = clock.textsize(ip_address, font=tiny_font)
	clock.text((clock_area[2] - border - ip_w, clock_area[1]+ border), ip_address, font=tiny_font, fill=gray)
	# Frontlight level (out of 10):
	fl_w, fl_h = clock.textsize(conf["text"]["general"]["frontlight"]+str(frontlightLevel), font=tiny_font)
	clock.text((clock_area[2] - border - fl_w, clock_area[1] + ip_h + 2*border), conf["text"]["general"]["frontlight"]+str(frontlightLevel), font=tiny_font, fill=gray)
	# Battery percentage and status
	battery = str(int(readBatteryPercentage())) + "%"
	state = str(readBatteryState())
	battery_w, battery_h = clock.textsize(battery, font=tiny_font)
	state_w, state_h = clock.textsize(state, font=tiny_font)
	clock.text((clock_area[2] - border - state_w, clock_area[1] + 3*border+  ip_h +fl_h), state, font=tiny_font, fill=gray)
	clock.text((clock_area[2] - border - battery_w, clock_area[1] + 4*border+ip_h +fl_h+state_h), battery, font=tiny_font, fill=gray)
	# Draw reboot icon
	icon_size = 48
	big_border = 20
	clock_area_rebootBtn=[clock_area[0],clock_area[1],clock_area[0]+2*big_border+icon_size,clock_area[1]+icon_size+2*big_border]
	rebootImg = Image.open("icons/reboot.jpg").resize((icon_size,icon_size))
	img.paste(rebootImg,[clock_area_rebootBtn[0]+big_border,clock_area_rebootBtn[1]+big_border])
	# Draw wifi icon
	clock_area_wifiBtn=[clock_area[0],clock_area[1]+1*big_border+icon_size,clock_area[0]+2*big_border+icon_size,clock_area[1]+2*icon_size+4*big_border]
	if isWifiOn:
		wifi_onImg = Image.open("icons/wifi-on.jpg").resize((icon_size,icon_size))
		img.paste(wifi_onImg,[clock_area_wifiBtn[0]+big_border,clock_area_wifiBtn[1]+big_border])
	else:
		wifi_offImg = Image.open("icons/wifi-off.jpg").resize((icon_size,icon_size))
		img.paste(wifi_offImg,[clock_area_wifiBtn[0]+big_border,clock_area_wifiBtn[1]+big_border])
	# Draw frontlight icons
	clock_area_frontlightBtnUP=[clock_area[0],clock_area[1]+2*big_border+2*icon_size,clock_area[0]+2*big_border+icon_size,clock_area[1]+3*icon_size+5*big_border]
	clock_area_frontlightBtnDOWN=[clock_area[0],clock_area[1]+3*big_border+3*icon_size,clock_area[0]+2*big_border+icon_size,clock_area[1]+4*icon_size+6*big_border]
	frontlight_upImg = Image.open("icons/frontlight-up.jpg").resize((icon_size,icon_size))
	img.paste(frontlight_upImg,[clock_area_frontlightBtnUP[0]+big_border,clock_area_frontlightBtnUP[1]+big_border])
	frontlight_downImg = Image.open("icons/frontlight-down.jpg").resize((icon_size,icon_size))
	img.paste(frontlight_downImg,[clock_area_frontlightBtnDOWN[0]+big_border,clock_area_frontlightBtnDOWN[1]+big_border])
	# Draw invert colors icon
	clock_area_invertBtn=[clock_area[0],clock_area[1]+4*big_border+4*icon_size,clock_area[0]+2*big_border+icon_size,clock_area[1]+5*icon_size+7*big_border]
	frontlight_upImg = Image.open("icons/invert.jpg").resize((icon_size,icon_size))
	img.paste(frontlight_upImg,[clock_area_invertBtn[0]+big_border,clock_area_invertBtn[1]+big_border])
	# Clock
	clock_w, clock_h = clock.textsize(clockToDisplay, font=comfortaa_big)
	date_w, date_h = clock.textsize(dateToDisplay, font=comfortaa_small)
	clock.text((int(0.5*clock_area[2]-0.5*clock_w), int(0.5*clock_area[3]-0.6*clock_h)), clockToDisplay, font=comfortaa_big, fill=black)
	clock.text((max(int(0.5*clock_area[2]-0.5*date_w),10), int(0.5*clock_area[3]+0.7*clock_h)), dateToDisplay, font=comfortaa_small, fill=50)
	img.save(conf["imgPath"]["clock"])
	if useOldPrintImg:
		# # OLD WAY:
		mprintImg_path(conf["imgPath"]["clock"], 0, 0)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,0,0,img.width,img.height,raw_len)

def readBatteryPercentage():
	with open(conf["main"]["clock"]["batteryCapacityFile"]) as state:
		state.seek(0)
		res = ""
		for line in state:
			res += str(line)
	return res

def readBatteryState():
	res=""
	with open(conf["main"]["clock"]["batteryStatusFile"]) as percentage:
		percentage.seek(0)
		isFirst = True
		for line in percentage:
			if isFirst:
				res += str(line).rstrip()
				isFirst=False
	return res

def get_ip():
	global isWifiOn
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	try:
		# isWifiOn = True
		# doesn't even have to be reachable
		s.connect(('10.255.255.255', 1))
		IP = s.getsockname()[0]
	except:
		# isWifiOn = False
		if isWifiOn:
			IP = conf["text"]["general"]["wifiOnNotConnected"]
		else:
			# wifi is off so of course it is not connected
			IP = conf["text"]["general"]["wifiDisconnected"]
	finally:
		s.close()
	return IP

def onTouchClock(x,y):
	global clock_area_wifiBtn
	global frontlightLevel
	global clock_area_frontlightBtnUP
	global clock_area_frontlightBtnDOWN
	global clock_area_invertBtn
	global isNightMode
	relativex=x-clock_area[0]
	relativey=y-clock_area[1]
	if coordsInArea(relativex,relativey,clock_area_wifiBtn,True):
		if isWifiOn:
			threading.Thread(target=wifiDown).start()
			# wifiDown(True)
		else:
			threading.Thread(target=wifiUp).start()
			# wifiUp(True)
	elif coordsInArea(relativex,relativey,clock_area_rebootBtn,True):
		fbink_cfg_notification.row = 0
		fbink_cfg_notification.col = 18
		FBInk.fbink_print(fbfd, "Rebooting...", fbink_cfg_notification)
		mprintLog("Rebooting...")
		os.system("reboot")
	elif coordsInArea(relativex,relativey,clock_area_frontlightBtnUP,True):
		if frontlightLevel <10:
			frontlightLevel += 1
			setFrontlightLevel(frontlightLevel)
	elif coordsInArea(relativex,relativey,clock_area_frontlightBtnDOWN,True):
		if frontlightLevel>0:
			frontlightLevel -= 1
			setFrontlightLevel(frontlightLevel)
	elif coordsInArea(relativex,relativey,clock_area_invertBtn,False):
		if isNightMode:
			isNightMode = False
			fbink_cfg.is_nightmode = False
		else:
			isNightMode = True
			fbink_cfg.is_nightmode = True
		# Then refresh the screen, but inverted this time
		fbink_cfg.is_flashing = True
		FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, FBInk.HWD_PASSTHROUGH, fbink_cfg)
		fbink_cfg.is_flashing = False
	else:
		mprintLog("Updating clock")
		printClock(time.time())

###############################################################################################
weather_lastData = []

def setupWeather():
	mprintLog("Weather Launched")
	weather_lastData = getWeather()
	if weather_lastData:
		printWeather(weather_lastData)
	now = int(time.time())
	hour = int(time.strftime("%-H", time.localtime(now)))
	minute = int(time.strftime("%M", time.localtime(now)))
	# next_day = math.ceil(int(time.time())/60)*60 + 60
	next_day = now + (24-hour)*3600 + int(updateWeatherAt)*3600 - minute*60
	# We wait for the next day
	time.sleep(int(next_day)-int(now))
	# Then we start it so that it updates every day (or every given time)
	while True :
		weather_lastData = getWeather()
		if not weather_lastData:
			break
		printWeather(weather_lastData)
		time.sleep(conf["main"]["weather"]["sleep"])

def getWeather():
	try:
		# response = requests.post(conf["main"]["weather"]["baseURL"], data = { 'APPID' : conf["main"]["weather"]["appid"], 'id' : conf["main"]["weather"]["city"],'units':'metric'})
		response = requests.get("http://api.openweathermap.org/data/2.5/forecast?id=" + conf["main"]["weather"]["city"] + "&units=metric&APPID=" + conf["main"]["weather"]["appid"])
		mprintLog("Weather response code :"+str(response.status_code))
		if response.status_code == 200:
			weatherData_json = response.content
			weatherData = json.loads(weatherData_json)
			return weatherData
		else:
			return False
	except:
		return False

def printWeather(weatherData):
	"""
	"""
	# Designing borders and sizes :
	border = 10

	# Building main image
	img = Image.new('L', (weather_area[2]-weather_area[0], weather_area[3]-weather_area[1]-1), color=white)
	weatherImg = ImageDraw.Draw(img, 'L')
	weatherImg.text((border,border), weatherData["city"]["name"], font=tiny_font, fill=50)
	todaytext_w, todaytext_h = weatherImg.textsize(conf["text"]["weather"]["today"], font=small_font_bold)
	weatherImg.text((int(0.5*weather_area_today[2]-0.5*todaytext_w),border), conf["text"]["weather"]["today"] , font=small_font_bold, fill=black)

	wind_arrow = Image.open("icons/wind_arrow.png")

	# Separation lines :
	weatherImg.line([weather_area_today[2],weather_area_today[1],weather_area_today[2],weather_area_today[3]], gray)	#Main separation today/coming days
	weatherImg.line([weather_area_t9[0],weather_area_t9[1],weather_area_t6[2],weather_area_t6[3]],200)		#Small line between 8h and 11h
	weatherImg.line([weather_area_t12[0],weather_area_t12[1],weather_area_t9[2],weather_area_t9[3]],200)		#Small line between 11h and 14h
	weatherImg.line([weather_area_t15[0],weather_area_t15[1],weather_area_t12[2],weather_area_t12[3]],200)		#Small line between ... etc
	weatherImg.line([weather_area_t18[0],weather_area_t18[1],weather_area_t15[2],weather_area_t15[3]],200)		#Small line between ... etc
	weatherImg.line([weather_area_t21[0],weather_area_t21[1],weather_area_t18[2],weather_area_t18[3]],200)		#Small line between ... etc

	# Building hourly forecast for today (if exist, else leave space empty because the time has already passed)
	# if starting the script at midniht, there migght be some bugs. Here is a fix attempt:
	if time.strftime("%x", time.gmtime(int(float(weatherData["list"][0]["dt"])))) == time.strftime("%x", time.gmtime(time.time())):
		i=0
	else:
		i=1
	while time.strftime("%x", time.gmtime(int(float(weatherData["list"][i]["dt"])))) == time.strftime("%x", time.gmtime(time.time())):
		# while we are looking at Today's forecast
		hour = time.strftime("%-H", time.gmtime(int(float(weatherData["list"][i]["dt"]))))
		hour_local = time.strftime("%-H", time.localtime(int(float(weatherData["list"][i]["dt"]))))
		condition = Image.open("icons/" + weatherData["list"][i]["weather"][0]["icon"] + ".png")
		condition_size = weather_area_t6[2]-weather_area_t6[0]-5*border
		condition_resized = condition.resize((condition_size, condition_size))
		temp_w,temp_h = weatherImg.textsize("3.4552 M/s", font=tiny_font)
		if 'temp' in weatherData["list"][i]["main"]:
			temp = str(weatherData["list"][i]["main"]["temp"])
		else:
			temp = "?"
		if 'clouds' in weatherData["list"][i]:
			clouds = str(weatherData["list"][i]["clouds"]["all"])
		else:
			clouds = "0"
		if 'rain' in weatherData["list"][i] and '3h' in weatherData["list"][i]["rain"]:
			rain = str(weatherData["list"][i]["rain"]["3h"])
		else:
			rain = "0"
		if 'wind' in weatherData["list"][i]:
			wind = str(weatherData["list"][i]["wind"]["speed"])
			windRot=int(weatherData["list"][i]["wind"]["deg"])
		else:
			wind= "0"
			windRot=0
		area_to_call = "weather_area_t"+str(hour)
		eval(area_to_call)
		weatherImg.text((eval(area_to_call)[0]+border*3,eval(area_to_call)[1] + border), hour_local + "h", font=tiny_font, fill=black)
		img.paste(condition_resized,[eval(area_to_call)[0]+2*border,eval(area_to_call)[1]+temp_h+border])
		weatherImg.text((eval(area_to_call)[0]+border,eval(area_to_call)[1] + condition_size + temp_h + 3*border), temp + "deg", font=tiny_font, fill=50)
		weatherImg.text((eval(area_to_call)[0]+border,eval(area_to_call)[1] + condition_size + 2*temp_h + 4*border), clouds + "%", font=tiny_font, fill=50)
		weatherImg.text((eval(area_to_call)[0]+border,eval(area_to_call)[1] + condition_size + 3*temp_h + 5*border), rain + "mm", font=tiny_font, fill=50)
		weatherImg.text((eval(area_to_call)[0]+border,eval(area_to_call)[1] + condition_size + 4*temp_h + 6*border), wind + "m/s", font=tiny_font, fill=50)
		img.paste(wind_arrow.rotate((180+windRot)%360,fillcolor='white'),[eval(area_to_call)[0]+30,eval(area_to_call)[1] + condition_size + 5*temp_h +8*border])
		i+=1

	# Then the coming days :
	# Separation lines:
	weatherImg.line([weather_area_coming_day_2[0],weather_area_coming_day_2[1],weather_area_coming_day_1[2],weather_area_coming_day_1[3]],200)
	weatherImg.line([weather_area_coming_day_3[0],weather_area_coming_day_3[1],weather_area_coming_day_2[2],weather_area_coming_day_2[3]],200)

	# Now let's collect data for "tomorrow":
	tomorrow=[]
	while time.strftime("%x", time.gmtime(int(float(weatherData["list"][i]["dt"])))) == time.strftime("%x", time.gmtime(time.time()+60*60*24)):
		tomorrow.append(weatherData["list"][i])
		i += 1
	tomorrowPlusOne = []
	while time.strftime("%x", time.gmtime(int(float(weatherData["list"][i]["dt"])))) == time.strftime("%x", time.gmtime(time.time()+60*60*24*2)):
		tomorrowPlusOne.append(weatherData["list"][i])
		i += 1
	tomorrowPlusTwo = []
	while time.strftime("%x", time.gmtime(int(float(weatherData["list"][i]["dt"])))) == time.strftime("%x", time.gmtime(time.time()+60*60*24*3)):
		tomorrowPlusTwo.append(weatherData["list"][i])
		i += 1

	def condenseToAnotherInterval(data,local_beginning_hour,local_end_hour):
		appropriateData = []
		for forecast in data:
			hour = int(time.strftime("%-H", time.localtime(int(float(forecast["dt"])))))
			if hour>=local_beginning_hour and hour<=local_end_hour:
				appropriateData.append(forecast)
		icon=most_frequent([forecast["weather"][0]["icon"] for forecast in appropriateData])
		temp=average([forecast["main"]["temp"] for forecast in appropriateData])
		clouds=average([forecast["clouds"]["all"] for forecast in appropriateData])
		rain=sum([forecast["rain"]["3h"] if "rain" in forecast and "3h" in forecast["rain"] else 0 for forecast in appropriateData])
		wind=average([forecast["wind"]["speed"] for forecast in appropriateData])
		return {"icon":icon,"temp":int(round(temp)),"clouds":int(round(clouds)),"rain":round(rain,1),"wind":int(round(wind))}


	def printComingDay(name,data,area):
		day_AM=condenseToAnotherInterval(data,8,13)		#AM is from 8:00 to 13:00
		day_PM=condenseToAnotherInterval(data,14,21)	#PM is from 14:00 to 21:00
		# Name of the day
		daytext_w, daytext_h = weatherImg.textsize(name, font=small_font_bold)
		weatherImg.text((int(0.5*(area[2]+area[0])-0.5*daytext_w),area[1]+0.5*border), name , font=small_font_bold, fill=black)
		# Separation AM/PM
		weatherImg.line([int(0.5*(area[2]+area[0])),area[1]+40,int(0.5*(area[2]+area[0])),area[3]],200)
		# Text AM/text PM
		daySepText_w, daySepText_h = weatherImg.textsize("matin", font=tiny_font)
		weatherImg.text((int((1*area[2]+3*area[0])/4-0.5*daytext_w),area[1]+daytext_h+0.5*border), "Matin" , font=tiny_font, fill=50)
		weatherImg.text((int((3*area[2]+1*area[0])/4-0.5*daytext_w),area[1]+daytext_h+0.5*border), str("Apres-midi") , font=tiny_font, fill=50)
		# Icon AM/PM
		# condition_size = max(area[3]-area[1]-2*daytext_h-2*border,10)
		condition_size = max(area[3]-area[1]-8*border,10)
		condition_AM = Image.open("icons/" + day_AM["icon"] + ".png")
		condition_PM = Image.open("icons/" + day_PM["icon"] + ".png")
		condition_AM_resized = condition_AM.resize((condition_size, condition_size))
		condition_PM_resized = condition_PM.resize((condition_size, condition_size))
		img.paste(condition_AM_resized,[int(area[0]+0.5*border),int(area[3]-1*border-condition_size)])
		img.paste(condition_PM_resized,[int(0.5*(area[2]+area[0])+0.5*border),int(area[3]-1*border-condition_size)])
		# Temp / clouds AM/PM
		weatherImg.text((int(area[0]+border+condition_size),int(area[3]-1*border-condition_size)), str(day_AM["temp"]) + "deg / " + str(day_AM["clouds"]) + "%" , font=tiny_tiny_font, fill=gray)
		weatherImg.text((int(0.5*(area[2]+area[0])+border+condition_size),int(area[3]-1*border-condition_size)), str(day_PM["temp"]) + "deg / " + str(day_PM["clouds"]) + "%" , font=tiny_tiny_font, fill=gray)
		# Rain/Wind AM/PM
		weatherImg.text((int(area[0]+border+condition_size),int(area[3]-1.5*border-condition_size+daySepText_h)), str(day_AM["rain"]) + "mm / " + str(day_AM["wind"]) + "m/s" , font=tiny_tiny_font, fill=gray)
		weatherImg.text((int(0.5*(area[2]+area[0])+border+condition_size),int(area[3]-1.5*border-condition_size+daySepText_h)), str(day_PM["rain"]) + "mm / " + str(day_PM["wind"]) + "m/s" , font=tiny_tiny_font, fill=gray)


	printComingDay(conf["text"]["weather"]["tomorrow"],tomorrow,weather_area_coming_day_1)
	printComingDay(time.strftime("%A", time.localtime(time.time()+60*60*24*2)),tomorrowPlusOne,weather_area_coming_day_2)
	printComingDay(time.strftime("%A", time.localtime(time.time()+60*60*24*3)),tomorrowPlusTwo,weather_area_coming_day_3)


	# Printing image
	if useOldPrintImg:
		# OLD WAY:
		img.save(conf["imgPath"]["weather"])
		mprintImg_path(conf["imgPath"]["weather"], weather_area[0], weather_area[1]+1)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,weather_area[0], weather_area[1]+1,img.width,img.height,raw_len)
	# fbink_cfg_weather.row = 16
	# fbink_cfg_weather.col = 1
	# FBInk.fbink_print(fbfd, "Here is the weather : good enough", fbink_cfg_weather)
	return True

def onTouchWeather(x,y):
	return True

def most_frequent(List):
	dict = {}
	count, itm = 0, ''
	for item in reversed(List):
		dict[item] = dict.get(item, 0) + 1
		if dict[item] >= count:
			count, itm = dict[item], item
	return (itm)

def average(lst):
	return sum(lst) / len(lst)

###############################################################################################
current_calendar_view = "week"
current_calendar_eventBeingEdited=False 	#Holds the new data event we are editing (or creating)
current_calendar_eventBeingEdited_beforeEdit=False
current_calendar_isEditMode = False			#Holds the event number if in edit mode
current_calendar_eventsAreas = [[] for i in range(len(calendar_area_days))]			#Relative position of the events within a day area
current_week_starting_day = 0
current_day_number=0
calendar_data={}
calendar_filepath = "files/calendar.json"
runeStr=""
last_text_box_used = ""
sample_event={"beginHour":16,"endHour":18,"title":"New Event","color":14}

def setupCalendar():
	global calendar_data
	calendar_data = getCalendarDataFromFile(calendar_filepath)
	now=time.time()
	now = convertTimestampToXoclock(now,10)
	weekday = (int(time.strftime("%w", time.gmtime(now)))-1)%conf["main"]["calendar"]["numberOfDaysOnScreen"] 	#weekday, starting on mondays
	current_week_starting_day = now - weekday*24*3600 				#First day of the week
	printCalendar_WeekView(calendar_data,current_week_starting_day)

def getCalendarDataFromFile(filePath):
	with open(filePath) as json_file:
		data = json.load(json_file)
		return data

def saveCalendarDataToFile(filePath,updated_calendar):
	with open(filePath,'w') as json_file:
		json.dump(updated_calendar,json_file,sort_keys=True,indent=4)
		return True

def extractSpecificDayData(full_data,week_starting_day,day_of_the_week):
	"""
	The goal here is to extract from the full dictionnary containing all the events for all the days one special day.
	The day is defined by being week_starting_day + day_of_the_week
	Timestamp as dictionnary entry are the timestamps at 10:00 UTC of the day in question
	"""
	week_starting_day = convertTimestampToXoclock(week_starting_day,10)
	day_timestamp =  week_starting_day+24*3600*day_of_the_week
	if str(day_timestamp) in full_data:
		return full_data[str(day_timestamp)]
	else:
		#returning empty day
		return {"main":{"timestamp":int(day_timestamp)},"events":[]}

def convertTimestampToXoclock(timestamp,X):
	"""
	Returns the timestamp corresponding to the same day, but at X o'clock
	"""
	hour = int(time.strftime("%-H", time.gmtime(timestamp)))
	minute = int(time.strftime("%M", time.gmtime(timestamp)))
	seconds = int(time.strftime("%S", time.gmtime(timestamp)))
	res = int(timestamp - seconds - 60*minute - 3600*(hour-X))
	return res

def printCalendar_WeekView(data,starting_day):
	global current_calendar_view
	global current_week_starting_day
	global keyboardCallFunction
	global isKeyboardMode
	current_calendar_view = "week"
	current_week_starting_day = starting_day
	keyboardCallFunction = False
	isKeyboardMode = False
	img = Image.new('L', (calendar_area[2]-calendar_area[0], calendar_area[3]-calendar_area[1]-2), color=white)
	cd = ImageDraw.Draw(img, 'L')
	border = 10

	# Separation lines between the days
	for i in range(len(calendar_area_days)-1):
		cd.line([calendar_area_days[i+1][0],calendar_area_days[i+1][1],calendar_area_days[i][2],calendar_area_days[i][3]], gray)	#Main separation today/coming days

	for i in range(len(calendar_area_days)):
		dayData = extractSpecificDayData(data,starting_day,i)
		if dayData:
			filei = printCalendar_singleDay(dayData,i)
		#then print the file at its place
			filei_opened= Image.open(filei)
			img.paste(filei_opened,[calendar_area_days[i][0]+1,calendar_area_days[i][1]])

	# Then print the icon to change week (by changing starting_day)

	# Then display image
	if useOldPrintImg:
		# OLD WAY:
		img.save(conf["imgPath"]["cd_weekView"])
		mprintImg_path(conf["imgPath"]["cd_weekView"], calendar_area[0], calendar_area[1]+1)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,calendar_area[0], calendar_area[1]+1,img.width,img.height,raw_len)
	return True

def printCalendar_singleDay(dayData,dayNumber):
	"""
	Returns the filepath of the created image
	"""
	global current_calendar_eventsAreas
	global calendar_area_weekView_weekChange_Forward
	global calendar_area_weekView_weekChange_Back
	border = 10
	img_day = Image.new('L', (calendar_area_days[0][2]-calendar_area_days[0][0]-1, calendar_area_days[0][3]-calendar_area_days[0][0]-1), color=white)
	cd_day = ImageDraw.Draw(img_day, 'L')
	# Name of the day
	dateToDisplay = time.strftime("%a %d %b", time.localtime(dayData["main"]["timestamp"]))
	day_w, day_h = cd_day.textsize(dateToDisplay, font=small_font)
	day_w_sample, day_h_sample = cd_day.textsize("SampleText1", font=small_font)
	# print(day_h_sample)
	cd_day.text((int(0.5*(calendar_area_days[0][2]+calendar_area_days[0][0])-0.5*day_w),calendar_area_days[0][1] + border), dateToDisplay , font=small_font, fill=black)
	# Events of the day
	event_area__ysize = calendar_area_days[0][3] - calendar_area_days[0][1] - day_h_sample-1*border
	event_area_beginy = int(calendar_area_days[0][1]+1*border+day_h_sample)
	event_first_hour_displayed=7
	event_last_hour_displayed=23
	size_of_one_event_hour = int(event_area__ysize / (event_last_hour_displayed - event_first_hour_displayed))
	current_calendar_eventsAreas[dayNumber] = [[0,0,0,0] for i in range(len(dayData["events"]))]
	for i in range(len(dayData["events"])):
		if not dayData["events"][i]:
			continue
		rectx=calendar_area_days[0][0]
		rectw=calendar_area_days[0][2]-calendar_area_days[0][0]-2
		recty= int(event_area_beginy + max(0,dayData["events"][i]["beginHour"]-event_first_hour_displayed)*size_of_one_event_hour)
		recth=int(size_of_one_event_hour*(dayData["events"][i]["endHour"]-dayData["events"][i]["beginHour"]))
		current_calendar_eventsAreas[dayNumber][i] = [rectx,recty,rectx+rectw,recty+recth]
		if "color" in dayData["events"][i]:
			rect_color = cv16BitsTo255(dayData["events"][i]["color"])
		else:
			rect_color = cv16BitsTo255(sample_event["color"])
		cd_day.rectangle([(rectx,recty),(rectx+rectw,recty+recth)],fill=rect_color,outline=50)
		hour_w, hour_h = cd_day.textsize(str('{0:g}'.format(float(dayData["events"][i]["endHour"]))), font=tiny_tiny_tiny_font)
		title_w, title_h = cd_day.textsize(str(dayData["events"][i]["title"].split("\r\n")[0][:15]), font=tiny_tiny_font)
		cd_day.text((rectx+0*border,recty+0*border),str('{0:g}'.format(float(dayData["events"][i]["beginHour"]))),font=tiny_tiny_tiny_font,fill=50)
		if 2*hour_h>recth:
			# In this case, we do not have enough room to display the hours on the top and bottom left corners.
			# So we display them
			cd_day.text((int(rectx+rectw-1*hour_w+0*border),recty+0*border),str('{0:g}'.format(float(dayData["events"][i]["endHour"]))),font=tiny_tiny_tiny_font,fill=50)
		else:
			cd_day.text((rectx+0*border,recty+recth-0*border-hour_h),str('{0:g}'.format(float(dayData["events"][i]["endHour"]))),font=tiny_tiny_tiny_font,fill=50)
		cd_day.text((int(rectx+0.5*rectw-0.5*title_w),int(recty+0.5*recth-0.5*title_h)),str(dayData["events"][i]["title"].split("\r\n")[0][:15]),font=tiny_tiny_font,fill=black)
	img_day.save("img/day" + str(dayNumber) + ".png")
	return "img/day" + str(dayNumber) + ".png"

textboxes_border = 30
def printCalendar_AddEventView(data,starting_day,day):
	# Re importing variables (could not quite figure out why it was necessary, but it is. Threading issue perhaps?)
	global current_calendar_view
	global current_week_starting_day
	global current_day_number
	global current_calendar_eventBeingEdited  #This one is necessary
	global current_calendar_isEditMode
	global calendar_area_addEvent_Back
	global calendar_area_addEvent_Save
	global calendar_area_addEvent_Delete
	global calendar_area_addEvent_Textboxes_area
	current_calendar_view = "add"
	current_week_starting_day = starting_day
	current_day_number = day

	img = Image.new('L', (calendar_area[2]-calendar_area[0], calendar_area[3]-calendar_area[1]-2), color=white)
	cd = ImageDraw.Draw(img, 'L')
	cd.line([calendar_area_days[1][0],calendar_area_days[1][1],calendar_area_days[0][2],calendar_area_days[0][3]], gray)	#Main separation
	# Print the specific day on the left:
	dayData = extractSpecificDayData(data,starting_day,day)
	day_img = "img/day" + str(day) + ".png"
	day_img_opened= Image.open(day_img)
	img.paste(day_img_opened,[0,0])
	# Then print some help text
	helptext_w, helptext_h = cd.textsize("Here is some sample helper text", font=tiny_font)
	if current_calendar_isEditMode:
		cd.text((calendar_area_days[1][0],calendar_area_days[1][3]-4*helptext_h-2*border),conf["text"]["calendar"]["editMode"] ,font=tiny_font,fill=0)
	else:
		cd.text((calendar_area_days[1][0],calendar_area_days[1][3]-4*helptext_h-2*border),conf["text"]["calendar"]["newEventMode"],font=tiny_font,fill=0)
	cd.text((calendar_area_days[1][0],calendar_area_days[1][3]-3*helptext_h-border),conf["text"]["calendar"]["helperText2"],font=tiny_font,fill=0)
	cd.text((calendar_area_days[1][0],calendar_area_days[1][3]-2*helptext_h),conf["text"]["calendar"]["helperText3"],font=tiny_font,fill=0)
	#Return icon, Save icon (and delete icon if we are in event modification)
	save_img = "icons/save.png"
	back_img = "icons/back.png"
	delete_img = "icons/delete.jpg"
	icon_size=50
	save_img_opened= Image.open(save_img).resize((icon_size,icon_size))
	back_img_opened= Image.open(back_img).resize((icon_size,icon_size))
	delete_img_opened= Image.open(delete_img).resize((icon_size,icon_size))
	calendar_area_addEvent_Save=[calendar_area_days[-1][2]-icon_size-textboxes_border,calendar_area_days[-1][3]-icon_size-textboxes_border,calendar_area_days[-1][2],calendar_area_days[-1][3]]
	calendar_area_addEvent_Back=[calendar_area_days[-1][2]-icon_size*2-2*textboxes_border,calendar_area_days[-1][3]-icon_size-textboxes_border,calendar_area_days[-1][2]-icon_size-textboxes_border,calendar_area_days[-1][3]]
	calendar_area_addEvent_Delete=[calendar_area_days[-1][2]-icon_size*3-3*textboxes_border,calendar_area_days[-1][3]-icon_size-textboxes_border,calendar_area_days[-1][2]-icon_size*2-2*textboxes_border,calendar_area_days[-1][3]]
	img.paste(save_img_opened,[calendar_area_addEvent_Save[0],calendar_area_addEvent_Save[1]])
	img.paste(back_img_opened,[calendar_area_addEvent_Back[0],calendar_area_addEvent_Back[1]])
	img.paste(delete_img_opened,[calendar_area_addEvent_Delete[0],calendar_area_addEvent_Delete[1]])
	#Finally,display everything
	img.save("img/full_calendar_dayView.png")
	if useOldPrintImg:
		# OLD WAY:
		mprintImg_path("img/full_calendar_dayView.png", calendar_area[0], calendar_area[1]+1)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,calendar_area[0], calendar_area[1]+1,img.width,img.height,raw_len)
	# Then print textboxes above everything
	calendar_area_addEvent_Textboxes_area = [calendar_area_days[1][0]+1,0,calendar_area[2],calendar_area[3]-calendar_area[1]-4*helptext_h-2*border]
	printCalendar_printTextboxesArea()

def printCalendar_printTextboxesArea():
	"""
	Returns the path to the image file containing ONLY the half with the textboxes.
	Advantage : can be called when editing the textboxes :
	Instead of re-drawing the whole area, it only redraws the part with the text
	"""
	global current_calendar_eventBeingEdited
	global current_calendar_isEditMode
	global calendar_area_addEvent_Textboxes_area
	global calendar_area_addEvent_beginHour
	global calendar_area_addEvent_endHour
	global calendar_area_addEvent_Title
	global calendar_area_addEvent_Color
	img = Image.new('L', (calendar_area_addEvent_Textboxes_area[2]-calendar_area_addEvent_Textboxes_area[0], calendar_area_addEvent_Textboxes_area[3]-calendar_area_addEvent_Textboxes_area[1]), color=white)
	cd_tb = ImageDraw.Draw(img, 'L')
	if current_calendar_eventBeingEdited == False and current_calendar_isEditMode==False:
		mprintLog("resetting current_calendar_isEditMode")
		current_calendar_eventBeingEdited = dict(sample_event)
	else:
		current_calendar_isEditMode = True #Make sure it is correctly set
		if not "color" in current_calendar_eventBeingEdited :
			current_calendar_eventBeingEdited["color"]=sample_event["color"]
		if not "title" in current_calendar_eventBeingEdited :
			current_calendar_eventBeingEdited["title"]=sample_event["title"]
		if not "beginHour" in current_calendar_eventBeingEdited :
			current_calendar_eventBeingEdited["beginHour"]=sample_event["beginHour"]
		if not "endHour" in current_calendar_eventBeingEdited :
			current_calendar_eventBeingEdited["endHour"]=sample_event["endHour"]
	bhour_w, bhour_h = cd_tb.textsize(str('{0:g}'.format(float(current_calendar_eventBeingEdited["beginHour"]))), font=small_font)
	ehour_w, ehour_h = cd_tb.textsize(str('{0:g}'.format(float(current_calendar_eventBeingEdited["endHour"]))), font=small_font)
	title_w, title_h = cd_tb.textsize(str(current_calendar_eventBeingEdited["title"]), font=small_font)
	color_w, color_h = cd_tb.textsize(str(current_calendar_eventBeingEdited["color"]), font=small_font)
	calendar_area_addEvent_beginHour=[calendar_area_days[1][0],calendar_area_days[1][1],calendar_area_days[1][0]+2*textboxes_border+bhour_w,calendar_area_days[1][1]+2*textboxes_border+bhour_h]
	calendar_area_addEvent_endHour=[calendar_area_days[-1][2]-2*textboxes_border-ehour_w,calendar_area_days[-1][1],calendar_area_days[-1][2],calendar_area_days[-1][1]+2*textboxes_border+ehour_h]
	calendar_area_addEvent_Title=[int((calendar_area_days[-1][2]+calendar_area_days[1][0])*0.5-0.5*title_w-textboxes_border),int((calendar_area_days[-1][3]+calendar_area_days[1][1])*0.5-1*title_h+15-textboxes_border),int((calendar_area_days[-1][2]+calendar_area_days[1][0])*0.5+0.5*title_w+textboxes_border),int((calendar_area_days[-1][3]+calendar_area_days[1][1])*0.5+0.5*title_h+textboxes_border)]
	calendar_area_addEvent_Color=[int((calendar_area_days[-1][2]+calendar_area_days[1][0])*0.5-0.5*color_w-textboxes_border),calendar_area_days[1][1],int((calendar_area_days[-1][2]+calendar_area_days[1][0])*0.5+0.5*color_w+textboxes_border),calendar_area_days[1][1]+2*textboxes_border+color_h]
	cd_tb.text((calendar_area_addEvent_beginHour[0]+1*textboxes_border-calendar_area_days[1][0],calendar_area_addEvent_beginHour[1]+1*textboxes_border),str('{0:g}'.format(float(current_calendar_eventBeingEdited["beginHour"]))),font=small_font,fill=50)
	cd_tb.text((calendar_area_addEvent_endHour[0]+1*textboxes_border-calendar_area_days[1][0],calendar_area_addEvent_endHour[1]+1*textboxes_border),str('{0:g}'.format(float(current_calendar_eventBeingEdited["endHour"]))),font=small_font,fill=50)
	cd_tb.text((calendar_area_addEvent_Title[0]+1*textboxes_border-calendar_area_days[1][0],calendar_area_addEvent_Title[1]+1*textboxes_border),str(current_calendar_eventBeingEdited["title"]),font=small_font,fill=10)
	cd_tb.text((calendar_area_addEvent_Color[0]+1*textboxes_border-calendar_area_days[1][0],calendar_area_addEvent_Color[1]+1*textboxes_border),str(current_calendar_eventBeingEdited["color"]),font=small_font,fill=cv16BitsTo255(int(current_calendar_eventBeingEdited["color"])))
	if useOldPrintImg:
		# OLD WAY:
		tb_img = "img/cd_textboxes.png"
		img.save(tb_img)
		mprintImg_path(tb_img, calendar_area[0]+calendar_area_addEvent_Textboxes_area[0],calendar_area[1]+calendar_area_addEvent_Textboxes_area[1]+1)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,calendar_area[0]+calendar_area_addEvent_Textboxes_area[0],calendar_area[1]+calendar_area_addEvent_Textboxes_area[1]+1,img.width,img.height,raw_len)
	return True

def saveEvent(eventData,fullData,week_starting_day,day_of_the_week):
	"""
	Saves the event to the correct location in the global calendar_data variable
	"""
	global calendar_data
	mprintLog("adding event"+str(eventData))
	if eventData["beginHour"] > eventData["endHour"]:
		mprintLog("Reversing beginHour and endHour")
		temp=eventData["beginHour"]
		eventData["beginHour"] = eventData["endHour"]
		eventData["endHour"] = temp
	targetTimestamp = convertTimestampToXoclock(week_starting_day+day_of_the_week*24*3600,10)
	if not str(targetTimestamp) in fullData:
		#Creating the day reference
		fullData[str(targetTimestamp)] = {"main":{"timestamp":targetTimestamp},"events":[]}
	fullData[str(targetTimestamp)]["events"].append(eventData)
	calendar_data = fullData
	return calendar_data

def deleteEvent(eventData,fullData,week_starting_day,day_of_the_week):
	"""
	returns the updated calendar. If event exists, is deleted
	"""
	global calendar_data
	mprintLog("Deleting event" + str(eventData))
	targetTimestamp = convertTimestampToXoclock(week_starting_day+day_of_the_week*24*3600,10)
	if str(targetTimestamp) in fullData:
		if eventData in fullData[str(targetTimestamp)]["events"]:
			fullData[str(targetTimestamp)]["events"].remove(eventData)
			mprintLog("1 event removed")
	calendar_data = fullData
	return calendar_data

def keyboard_cd_beginHour(key):
	global current_calendar_eventBeingEdited
	global last_text_box_used
	if not last_text_box_used == "beginHour":
		keyboard_reinitVariable()
		last_text_box_used = "beginHour"
	beginHour = keyboard_appendKeyToString(key)
	if not current_calendar_eventBeingEdited:
		current_calendar_eventBeingEdited = sample_event
	try:
		current_calendar_eventBeingEdited["beginHour"] = float(beginHour)
	except:
		current_calendar_eventBeingEdited["beginHour"] = sample_event["beginHour"]
	printCalendar_printTextboxesArea()

def keyboard_cd_endHour(key):
	global current_calendar_eventBeingEdited
	global last_text_box_used
	if not last_text_box_used == "endHour":
		keyboard_reinitVariable()
		last_text_box_used = "endHour"
	endHour = keyboard_appendKeyToString(key)
	if not current_calendar_eventBeingEdited:
		current_calendar_eventBeingEdited = sample_event
	try:
		current_calendar_eventBeingEdited["endHour"] = float(endHour)
	except:
		current_calendar_eventBeingEdited["endHour"] = sample_event["endHour"]
	printCalendar_printTextboxesArea()

useFastTextInput = False  # False recommended (WIP)
def keyboard_cd_Title(key):
	global current_calendar_eventBeingEdited
	global calendar_data
	global current_week_starting_day
	global current_day_number
	global last_text_box_used
	global runeStr
	if not last_text_box_used == "Title":
		# If the last time the keyboard was called was not for the same textbox
		# We reset the global variable containing the string being typed
		keyboard_reinitVariable()
		# We say that we now are editing this textbox
		last_text_box_used = "Title"
		# And (specific to the title), we want to edit the current title string, not start anew, so we fetch the title string
		if current_calendar_eventBeingEdited and 'title' in current_calendar_eventBeingEdited:
			runeStr = current_calendar_eventBeingEdited["title"]
	title = keyboard_appendKeyToString(key)
	if not current_calendar_eventBeingEdited:
		current_calendar_eventBeingEdited = sample_event
	try:
		current_calendar_eventBeingEdited["title"] = str(title)
	except:
		current_calendar_eventBeingEdited["title"] = sample_event["title"]

	if not useFastTextInput:
		# # VERY OLD SOLUTION : for each new character, print the whole area image again
		# printCalendar_AddEventView(calendar_data,current_week_starting_day,current_day_number)
		# NEWER SOLUTION : print only the textboxes area:
		printCalendar_printTextboxesArea()
	else:
		# # Let's do this better : print only the specific text using fbink's openType and truetype support

		fbink_ot_cfg.margins.top = 500
		fbink_ot_cfg.margins.bottom = 600
		fbink_ot_cfg.margins.left = 400
		fbink_ot_cfg.margins.right = 50
		fbink_ot_cfg.size_px = 26
		fbink_ot_cfg.is_formatted = True
		FBInk.fbink_print_ot(fbfd, str(current_calendar_eventBeingEdited["title"]), fbink_ot_cfg, fbink_cfg, ffi.NULL);
		# # # NOTE : I once again was not able to use the Python bindings, so let's call use a bash command (yeah...)
		# # NOT A DECENT SOLUTION : text might be executed by shell if passing a string containing '
		# # And when erasing, it does not erase previously written text
		# # And not hiding the text already here
		# # And hard to use and properly define
		# os.system("fbink -t regular=fonts/Merriweather-Regular.ttf,bold=fonts/Merriweather-Bold.ttf,italic=fonts/Merriweather-RegularItalic.ttf,bolditalic=fonts/Merriweather-BoldItalic.ttf,size=10,top=500,bottom=600,left=400,right=50,format '" + str(current_calendar_eventBeingEdited["title"]) +"'")

def keyboard_cd_Color(key):
	global current_calendar_eventBeingEdited
	global last_text_box_used
	if not last_text_box_used == "Color":
		keyboard_reinitVariable()
		last_text_box_used = "Color"
	color = keyboard_appendKeyToString(key)
	if not current_calendar_eventBeingEdited:
		current_calendar_eventBeingEdited = sample_event
	try:
		if int(color)>=0 and int(color)<=16:
			current_calendar_eventBeingEdited["color"] = int(color)
		else:
			current_calendar_eventBeingEdited["color"] = sample_event["color"]
	except:
		current_calendar_eventBeingEdited["color"] = sample_event["color"]
	printCalendar_printTextboxesArea()

def keyboard_reinitVariable():
	global runeStr
	global upperCase
	runeStr = ""
	upperCase = False

upperCase=False
def keyboard_appendKeyToString(k):
	global runeStr
	global upperCase
	if not k["isKey"]:
		return runeStr
	if k["keyType"] == osk.KTstandardChar:
		if upperCase:
			key = str(k["keyCode"]).upper()
		else:
			key = str(k["keyCode"]).lower()
		runeStr = runeStr + key
	elif k["keyType"] == osk.KTbackspace:
		if len(runeStr) > 0:
			# removing last element and drawing and empty space instead
			runeStr = runeStr[:-1]
	elif k["keyType"] == osk.KTcapsLock:
		if upperCase:
			upperCase = False
		else:
			upperCase = True
	elif k["keyType"] == osk.KTcarriageReturn:
		runeStr += "\r\n"
	return runeStr

def onTouchCalendar(x,y):
	relativex=x-calendar_area[0]
	relativey=y-calendar_area[1]
	global current_calendar_view
	global current_calendar_eventBeingEdited
	global current_week_starting_day
	global current_day_number
	global keyboardCallFunction
	global last_text_box_used
	global current_calendar_eventsAreas
	global current_calendar_isEditMode
	global calendar_area_weekView_weekChange_Forward
	global calendar_area_weekView_weekChange_Back
	global current_calendar_eventBeingEdited_beforeEdit
	global calendar_area_addEvent_Textboxes_area
	if current_calendar_view == "week":
		if coordsInArea(relativex,relativey,calendar_area_weekView_weekChange_Back):
			current_week_starting_day=convertTimestampToXoclock(int(current_week_starting_day-conf["main"]["calendar"]["numberOfDaysOnScreen"]*24*3600),10)
			calendar_data = getCalendarDataFromFile(calendar_filepath)
			printCalendar_WeekView(calendar_data,current_week_starting_day)
		elif coordsInArea(relativex,relativey,calendar_area_weekView_weekChange_Forward):
			current_week_starting_day=convertTimestampToXoclock(int(current_week_starting_day+conf["main"]["calendar"]["numberOfDaysOnScreen"]*24*3600),10)
			calendar_data = getCalendarDataFromFile(calendar_filepath)
			printCalendar_WeekView(calendar_data,current_week_starting_day)
		else:
			for i in range(len(calendar_area_days)):
				if coordsInArea(relativex,relativey,calendar_area_days[i]):
					calendar_data = getCalendarDataFromFile(calendar_filepath)
					printCalendar_AddEventView(calendar_data,current_week_starting_day,i)
	else:
		if coordsInArea(relativex,relativey,calendar_area_days[0]):
			very_relativex=calendar_area_days[0][0]+1 	#dirty workaround. the x coordinates here does not quite matter
			for i in range(len(current_calendar_eventsAreas[current_day_number])):
				if coordsInArea(very_relativex,relativey,current_calendar_eventsAreas[current_day_number][i]):
					#User clicked on an event to edit it.
					current_calendar_isEditMode = i
					calendar_data = getCalendarDataFromFile(calendar_filepath)
					current_calendar_eventBeingEdited = calendar_data[str(convertTimestampToXoclock(int(current_week_starting_day+24*3600*current_day_number),10))]["events"][i]
					current_calendar_eventBeingEdited_beforeEdit = dict(current_calendar_eventBeingEdited)
					printCalendar_AddEventView(calendar_data,current_week_starting_day,current_day_number)
		elif coordsInArea(relativex,relativey,calendar_area_addEvent_Textboxes_area):
			if coordsInArea(relativex,relativey,calendar_area_addEvent_beginHour):
				printKeyboard()
				keyboardCallFunction = keyboard_cd_beginHour
			elif coordsInArea(relativex,relativey,calendar_area_addEvent_endHour):
				printKeyboard()
				keyboardCallFunction = keyboard_cd_endHour
			elif coordsInArea(relativex,relativey,calendar_area_addEvent_Title):
				printKeyboard()
				keyboardCallFunction = keyboard_cd_Title
			elif coordsInArea(relativex,relativey,calendar_area_addEvent_Color):
				printKeyboard()
				keyboardCallFunction = keyboard_cd_Color
		elif coordsInArea(relativex,relativey,calendar_area_addEvent_Save):
			#Save the event and delete the previous one if we are in editing mode
			calendar_data = getCalendarDataFromFile(calendar_filepath)
			if current_calendar_isEditMode != False and current_calendar_eventBeingEdited_beforeEdit != False:
				calendar_data = deleteEvent(current_calendar_eventBeingEdited_beforeEdit,calendar_data,current_week_starting_day,current_day_number)
			updated_calendar = saveEvent(current_calendar_eventBeingEdited,calendar_data,current_week_starting_day,current_day_number)
			saveCalendarDataToFile(calendar_filepath,updated_calendar)
			printCalendar_WeekView(updated_calendar,current_week_starting_day)
			current_calendar_eventBeingEdited = False
			current_calendar_eventBeingEdited_beforeEdit = False
			current_calendar_isEditMode = False
			last_text_box_used = False
			hideKeyboard()
		elif coordsInArea(relativex,relativey,calendar_area_addEvent_Back):
			hideKeyboard()
			calendar_data = getCalendarDataFromFile(calendar_filepath)
			printCalendar_WeekView(calendar_data,current_week_starting_day)
			current_calendar_eventBeingEdited = False
			current_calendar_eventBeingEdited_beforeEdit = False
			current_calendar_isEditMode = False
			last_text_box_used = False
		elif coordsInArea(relativex,relativey,calendar_area_addEvent_Delete):
			hideKeyboard()
			calendar_data = getCalendarDataFromFile(calendar_filepath)
			updated_calendar = deleteEvent(current_calendar_eventBeingEdited_beforeEdit,calendar_data,current_week_starting_day,current_day_number)
			saveCalendarDataToFile(calendar_filepath,updated_calendar)
			printCalendar_WeekView(updated_calendar,current_week_starting_day)
			current_calendar_eventBeingEdited = False
			current_calendar_eventBeingEdited_beforeEdit = False
			current_calendar_isEditMode = False
			last_text_box_used = False

###############################################################################################
def getRandomQuoteFromFile():
	return True

def printQuote():
	return True

###############################################################################################
def printBackground():
	"""
	First time only
	"""
	# Init image
	img = Image.new('L', (screen_width, screen_height+1), color=white)
	bg = ImageDraw.Draw(img, 'L')
	border=10
	# Draw lines in the middle of the screen
	bg.line([border,clock_area[3],screen_width-border, clock_area[3]], gray)
	bg.line([border,weather_area[3],screen_width-border, weather_area[3]], gray)
	bg.line([border,notification_area[3],screen_width-border, notification_area[3]], gray)
	bg.line([border,calendar_area[3],screen_width-border, calendar_area[3]], gray)
	# Saving background and displaying it
	img.save(conf["imgPath"]["background"])
	if useOldPrintImg:
		# OLD WAY:
		mprintImg_path(conf["imgPath"]["background"], 0, 0)
	else:
		# NEW WAY:
		raw_data=img.tobytes("raw")
		raw_len = len(raw_data)
		mprintImg(raw_data,0,0,img.width,img.height,raw_len)
	return True

def touchDriverFc_old():
	"""
	Unused, with a more basic and frustrating debounce system
	"""
	last_touch = time.time()
	while True:
		(x, y, err) = t.getInput()
		if timeDelta(last_touch,time.time())<conf["main"]["general"]["touchDebounceTime"]:
			mprintLog("Debouncing")
		else:
			mprintLog("Not deboucning")
			last_touch=time.time()
			k = vk.getPressedKey(x, y)
			if isKeyboardMode and k!= None:
				#If the keyboard is displayed, and we pressed on a key, just call the function that deals with the keyboard entry
				keyboardCallFunction(k)
			else:
				if coordsInArea(x,y,clock_area):
					onTouchClock(x,y)
				elif coordsInArea(x,y,calendar_area):
					onTouchCalendar(x,y)
				elif coordsInArea(x,y,weather_area):
					onTouchWeather(x,y)
				elif coordsInArea(x,y,notification_area):
					onTouchNotification(x,y)

def touchDriverFc():
	last_touch_time = time.time()
	last_touch_area = [-conf["main"]["general"]["touchDebounceAreaSize"]-1,-conf["main"]["general"]["touchDebounceAreaSize"]-1,-1,-1]
	global isKeyboardMode
	global keyboardCallFunction

	while True:
		try:
			(x, y, err) = t.getInput()
		except:
			continue
		if t.debounceAllow(x,y):
			k = vk.getPressedKey(x, y)
			if isKeyboardMode and k!= None:
				#If the keyboard is displayed, and we pressed on a key, just call the function that deals with the keyboard entry
				keyboardCallFunction(k)
			else:
				if coordsInArea(x,y,clock_area):
					onTouchClock(x,y)
				elif coordsInArea(x,y,calendar_area):
					onTouchCalendar(x,y)
				elif coordsInArea(x,y,weather_area):
					onTouchWeather(x,y)
				elif coordsInArea(x,y,notification_area):
					onTouchNotification(x,y)

def printKeyboard():
	#First, make a dump (a copy of what is behind the keyboard)
	global isKeyboardMode #Necessary
	global fbink_dumpcfg
	if isKeyboardMode:
		return False
	else:
		isKeyboardMode = True
		fbink_dumpcfg = ffi.new("FBInkDump *") # resetting dump (don't know if needed)
		FBInk.fbink_region_dump(fbfd,int(vk.StartCoords["X"]),int(vk.StartCoords["Y"]),int(vk.widthPX),int(vk.heightPX)+2,fbink_cfg,fbink_dumpcfg)
		mprintImg_path(vkPNG, int(vk.StartCoords["X"]), int(vk.StartCoords["Y"]))
		return True

def hideKeyboard():
	#We restore the copy of what was behind the keyboard
	global isKeyboardMode #Necessary
	# if isKeyboardMode:
	global fbink_dumpcfg
	try:
		mprintLog("Restoring dump")
		isKeyboardMode = False
		FBInk.fbink_restore(fbfd,fbink_cfg,fbink_dumpcfg)
		return True
	except:
		isKeyboardMode = True
		mprintLog("Could not restore dump, staying in keyboard mode")
		return False

###############################################################################################

def terminate_thread(thread):
	"""Terminates a python thread from another thread.

	:param thread: a threading.Thread instance
	"""
	if not thread.isAlive():
		return

	exc = ctypes.py_object(SystemExit)
	res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
		ctypes.c_long(thread.ident), exc)
	if res == 0:
		raise ValueError("nonexistent thread id")
	elif res > 1:
		# """if it returns a number greater than one, you're in trouble,
		# and you should call it again with exc=NULL to revert the effect"""
		ctypes.pythonapi.PyThreadState_SetAsyncExc(thread.ident, None)
		raise SystemError("PyThreadState_SetAsyncExc failed")

def wifiDown(killHTTP=False):
	global httpd
	global isWifiOn
	if killHTTP:
		httpd.shutdown()
		terminate_thread(threads[0])
	try:
		mprintLog("Disabling wifi")
		os.system("sh ./files/disable-wifi.sh")
		isWifiOn = False
		mprintLog("Wifi disabled")
		printClock(time.time())
	except:
		mprintLog("Failed to disabled Wifi")

def wifiUp(restartHTTP=False):
	global isWifiOn
	try:
		mprintLog("Turning Wifi on")
		os.system("sh ./files/enable-wifi.sh")
		# os.system("sh ./files/obtain-ip.sh")
		# os.system(". ./files/nickel-usbms.sh && enable_wifi")
		mprintLog("Wifi should be enabled")
		time.sleep(1)
		isWifiOn = True
		printClock(time.time())
	except:
		mprintLog("Failed to enable wifi")
		mprintLog(str(sys.exc_info()[0]))
		mprintLog(str(sys.exc_info()[1]))
	if restartHTTP:
		try:
			mprintLog("restarting http server")
			threads[0].start()
		except:
			mprintLog("failed to restart http server")
			return False

def setFrontlightLevel(level):
	global frontlightLevel
	frontlightLevel= level
	# I want 10 levels, and I don't want them linear (especially because it might be useful to use the clock in the dark)
	# Could have used an exponential function to transform the input
	# But why shoud I do something easy when I can do something complicated ?
	if level == 0:
		actual_level=0
	elif level == 1:
		actual_level = 1
	elif level == 2:
		actual_level = 5
	elif level == 3:
		actual_level = 10
	elif level == 4:
		actual_level = 17
	elif level == 5:
		actual_level = 25
	elif level == 6:
		actual_level = 35
	elif level == 7:
		actual_level = 50
	elif level == 8:
		actual_level = 70
	elif level == 9:
		actual_level = 90
	elif level == 10:
		actual_level = 100
	l=int(actual_level)
	os.system("./files/frontlight " + str(l))

def cv16BitsTo255(x):
	return int(x*255/16)
def cv255To16Bits(x):
	return int(x*16/255)

def coordsInArea(x,y,area,invertArea=False):
	if x>=area[0] and x<area[2] and y>=area[1] and y<area[3]:
		if invertArea:
			touchIndicator(area)
		return True
	else:
		return False

def timeDelta(date1,date2):
	# returns the elapsed milliseconds between the two dates
	# TO DO : use the datetime library to make it more precise
	dt = date2 - date1
	return dt

def mprintImg_path(path,x,y):
	global isNightMode
	# try:
	if isNightMode:
		image = Image.open(str(path))
		inverted_image = PIL.ImageOps.invert(image)
		inverted_image.save(str(path)+"_inverted.png")
		FBInk.fbink_print_image(fbfd, str(path)+"_inverted.png".encode('ascii'), x, y, fbink_cfg)
	else:
		FBInk.fbink_print_image(fbfd, str(path).encode('ascii'), x, y, fbink_cfg)
	# except:
	# 	print("no image found at this path")

def mprintImg(raw_data,x,y,w,h,length=None):
	global isNightMode
	if length==None:
		length = len(raw_data)
	if isNightMode:
		fbink_cfg.is_nightmode = True
	else:
		fbink_cfg.is_nightmode = False
	# FBInk.fbink_print_image(fbfd, str(path).encode('ascii'), x, y, fbink_cfg)
	FBInk.fbink_print_raw_data(fbfd, raw_data, w, h, length, x, y, fbink_cfg)

def deleteTempImgFiles():
	"""
	If a img folder exists, delete its content. Else create it.
	"""
	print("Cleaning temp files")
	if os.path.exists("img"):
		for file in os.listdir("img/"):
			os.remove("img/" + file)
	else:
		os.mkdir('img')
	return True

def touchIndicator(area):
	def invertArea(type=0):
		if type==1:
			fbink_cfg.is_nightmode = True
		else:
			fbink_cfg.is_nightmode = False
		FBInk.fbink_refresh(fbfd, area[1], area[0], area[2]-area[0], area[3]-area[1], FBInk.HWD_PASSTHROUGH, fbink_cfg)
		if type==1:
			fbink_cfg.is_nightmode = False
		else:
			fbink_cfg.is_nightmode = True
	invertArea(1)
	threading.Timer(0.5,invertArea).start()
###############################################################################################
###############################################################################################


deleteTempImgFiles()

# INITIALIZING BACKGROUND.
printBackground()

# CLEAN REFRESH
fbink_cfg.is_flashing = True
FBInk.fbink_refresh(fbfd, 0, 0, 0, 0, FBInk.HWD_PASSTHROUGH, fbink_cfg)
fbink_cfg.is_flashing = False


# DISABLE FRONTLIGHT FIRST
setFrontlightLevel(frontlightLevel)
# ENABLE WIFI
isWifiOn = True
wifiUp(False)


# INITIALIZING KEYBOARD FOR FURTHER USE
with open('../Kobo-Python-OSKandUtils/sample-keymap-en_us.json') as json_file:
	km = json.load(json_file)
	vk = osk.virtKeyboard(km, screen_width, screen_height)
	# Generate an image of the OSK
	vkPNG = "img/vk.png"
	vk.createIMG(vkPNG)


# INITIALIZING TOUCH
touchPath = "/dev/input/event1"
t = KIP.inputObject(touchPath, screen_width, screen_height,conf["main"]["general"]["touchDebounceTime"],conf["main"]["general"]["touchDebounceAreaSize"])


#OTHER DETAILS :
# locale.setlocale(locale.LC_ALL, '') # French


# Launching different threads : different bits of code that will be executed at the same time
# threads = [threading.Thread(target=setupClock)]
threads = []
threads.append(threading.Thread(target=run))		 #MUST STAY AT INDEX 0
threads.append(threading.Thread(target=touchDriverFc))
threads.append(threading.Thread(target=setupClock))
threads.append(threading.Thread(target=setupWeather))
threads.append(threading.Thread(target=setupCalendar))
[thread.start() for thread in threads]
[thread.join() for thread in threads]
