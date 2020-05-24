#!/usr/bin/env python
################################################################################
##				IMPORTS
################################################################################
import sys
import json
sys.path.append('../Python-Screen-Stack-Manager')
import platform
import os
import threading
import requests
import math
import time
import locale
from base64 import b64decode
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
if platform.machine() in ["x86","AMD64","i686","x86_64"]:
	device = "Emulator"
else:
	device = "Kobo"
import pssm
################################################################################
##				Config and helper functions
################################################################################
with open('files/config.json') as json_file:
	conf = json.load(json_file)

def getHourFormatted(time_arg=time.time()):
	clockToDisplay = time.strftime("%H:%M", time.localtime(time_arg))
	dateToDisplay = time.strftime("%A %d %B %Y", time.localtime(time_arg))
	return (clockToDisplay,dateToDisplay)

def average(lst):
	return sum(lst) / len(lst) if len(lst)>0 else 0

def most_frequent(List):
	dict = {}
	count, itm = 0, ''
	for item in reversed(List):
		dict[item] = dict.get(item, 0) + 1
		if dict[item] >= count:
			count, itm = dict[item], item
	return (itm)

def getWeather():
	response = requests.get("http://api.openweathermap.org/data/2.5/forecast?id=" + conf["main"]["weather"]["city"] + "&units=metric&APPID=" + conf["main"]["weather"]["appid"])
	print("Weather response code :"+str(response.status_code))
	if response.status_code == 200:
		weatherData_json = response.content
		weatherData = json.loads(weatherData_json)
		return weatherData
	else:
		return None

################################################################################
##				Callback functions
################################################################################
def setupClock():
	now = time.time()
	next_minute = int((now+60)/60)*60
	wait  = next_minute - now + 1
	# We wait for the next minute
	screen.device.wait(wait)
	# Then we start it so that it updates every minute (or every given time)
	while True :
		hd = getHourFormatted(time.time())
		timeBtn.update(
			newAttributes={'text': hd[0]},
			skipPrint = True
			)
		dayBtn.update(
			newAttributes={'text': hd[1]}
		)
		screen.device.wait(conf["main"]["clock"]["sleep"])


################################################################################
##				HELPER CLASS
################################################################################
class Weather_Day(pssm.Layout):
	def __init__(self,weatherData=None,day=0,text="hey",**kwargs):
		self.weatherData = weatherData
		self.text = text
		self.day = day
		layout = self.build_layout(weatherData,day)
		super().__init__(layout)
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def condenseToAnotherInterval(self,data,local_beginning_hour,local_end_hour):
		appropriateData = []
		for forecast in data:
			hour = int(time.strftime("%H", time.localtime(int(float(forecast["dt"])))))
			if hour>=local_beginning_hour and hour<=local_end_hour:
				appropriateData.append(forecast)
		icon=most_frequent([forecast["weather"][0]["icon"] for forecast in appropriateData])
		temp=average([forecast["main"]["temp"] for forecast in appropriateData])
		clouds=average([forecast["clouds"]["all"] for forecast in appropriateData])
		rain=sum([forecast["rain"]["3h"] if "rain" in forecast and "3h" in forecast["rain"] else 0 for forecast in appropriateData])
		wind=average([forecast["wind"]["speed"] for forecast in appropriateData])
		return {"icon":icon,"temp":int(round(temp)),"clouds":int(round(clouds)),"rain":round(rain,1),"wind":int(round(wind))}

	def cleanData(self,weatherData,day):
		dayData=[]
		todayS = time.strftime("%x", time.gmtime(time.time()+60*60*24*day))
		i=0
		while time.strftime("%x", time.gmtime(int(weatherData["list"][i]["dt"]))) != todayS:
			i += 1
		while time.strftime("%x", time.gmtime(int(weatherData["list"][i]["dt"]))) == todayS:
			dayData.append(weatherData["list"][i])
			i += 1
		day_AM = self.condenseToAnotherInterval(dayData,8,13)		#AM is from 8:00 to 13:00
		day_PM = self.condenseToAnotherInterval(dayData,14,21)		#PM is from 14:00 to 21:00
		return (day_AM,day_PM)

	def build_layout(self,weatherData,day):
		halfDayData = self.cleanData(weatherData,day)
		dayBtn = pssm.Button(self.text,font_size="h*0.02",outline_color="white")
		morning = Weather_Day_Half(halfDayData[0],"Morning")
		afternoon = Weather_Day_Half(halfDayData[1],"Afternoon")
		layout = [
			["?/3", (dayBtn,"?")],
			["?"  , (morning,"?"), (pssm.Line(color="gray10",type="vertical"),1), (afternoon,"?")]
		]
		return layout

class Weather_Day_Half(pssm.Layout):
	def __init__(self,data=None,text="Hey",**kwargs):
		self.data = data
		self.text = text
		layout = self.build_layout(data,text)
		super().__init__(layout)
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def build_layout(self,data,text):
		icon = pssm.Static("icons/" + data["icon"] + ".png",centered = True)
		textBtn=pssm.Button(text,font_size="h*0.015",outline_color="white",font_color="gray2")
		info_text = str(data["temp"]) + "deg / " + str(data["clouds"]) + "%\n" + str(data["rain"]) + "mm / " + str(data["wind"]) + "m/s"
		infoBtn=pssm.Button(info_text,font_size="h*0.010",outline_color="white",font_color="gray5")
		layout = [
			["?",   (textBtn,"?")],
			["?*2", (icon,"?"), (infoBtn,"?*3")]
		]
		return layout

class Weather_Hour(pssm.Layout):
	def __init__(self,weatherData=None,hour=0,**kwargs):
		self.weatherData = weatherData
		layout = self.build_layout(weatherData,hour)
		super().__init__(layout)
		for param in kwargs:
			setattr(self, param, kwargs[param])

	def cleanData(self,weatherData,hour):
		res = {}
		i=hour
		res["hour"] = time.strftime("%H", time.gmtime(int(weatherData["list"][i]["dt"])))
		res["hour_local"] = time.strftime("%H", time.localtime(int(weatherData["list"][i]["dt"])))
		res["condition"] = "icons/" + weatherData["list"][i]["weather"][0]["icon"] + ".png"
		if 'temp' in weatherData["list"][i]["main"]:
			res["temp"] = str(weatherData["list"][i]["main"]["temp"])
		else:
			res["temp"] = "?"
		if 'clouds' in weatherData["list"][i]:
			res["clouds"] = str(weatherData["list"][i]["clouds"]["all"])
		else:
			res["clouds"] = "0"
		if 'rain' in weatherData["list"][i] and '3h' in weatherData["list"][i]["rain"]:
			res["rain"] = str(weatherData["list"][i]["rain"]["3h"])
		else:
			res["rain"] = "0"
		if 'wind' in weatherData["list"][i]:
			res["wind"] = str(weatherData["list"][i]["wind"]["speed"])
			res["windRot"]=int(weatherData["list"][i]["wind"]["deg"])
		else:
			res["wind"]= "0"
			res["windRot"]=0
		res["hour_local"] += "h"
		res["temp"] += " deg"
		res["clouds"] += "%"
		res["rain"] += "mm"
		res["wind"] += "m/s"
		return res

	def build_layout(self,weatherData,hour):
		layout = []
		res  = self.cleanData(weatherData,hour)
		data_text = res["temp"] + "\n" + res["clouds"] + "\n" + res["rain"]+ "\n" + res["wind"]
		hourBtn = pssm.Button(res["hour_local"],font_size = "h*0.018", outline_color = "white")
		conditionIcon = pssm.Icon(res["condition"])
		infoBtn = pssm.Button(data_text, font_size = "h*0.015",font_color="gray5", outline_color = "white")
		rot = (180+res["windRot"])%360
		wind_arrow = pssm.Static("icons/wind_arrow.png",rotation=rot,resize=False)
		layout.append(["?",(hourBtn,"?")])
		layout.append(["?*2",(conditionIcon,"?")])
		layout.append(["?*4",(infoBtn,"?")])
		layout.append(["?",(wind_arrow,"?")])
		return layout


class Calendar_Day(pssm.Layout):
	def __init__(self):
		return True



################################################################################
##				Clock Layout setup
################################################################################
# Icon bar
layout_iconBar = [
	["?", (pssm.Icon("reboot",centered = False),"w")],
	[10],
	["?", (pssm.Icon("wifi-on",centered = False),"w")],
	[10],
	["?", (pssm.Icon("frontlight-up",centered = False),"w")],
	[10],
	["?", (pssm.Icon("frontlight-down",centered = False),"w")],
	[10],
	["?", (pssm.Icon("invert",centered = False),"w")],
	[5]
]
iconBar = pssm.Layout(layout_iconBar)

# Clock and day
(clockToDisplay,dateToDisplay) = getHourFormatted()
timeBtn = pssm.Button(clockToDisplay, font_size = "h*0.15", outline_color="white")
dayBtn  = pssm.Button(dateToDisplay, font_size = "h*0.03", font_color="gray5", outline_color="white",text_yPosition = "top")
layout_clock = [
	["?*0.76", (timeBtn, "w*0.6")],
	["?*0.24", (dayBtn, "w*0.6")]
]
clock = pssm.Layout(layout_clock)

# Other information
infos = pssm.Button(
	text 		= "IP\n Frontlight \n Discharaging \n Percent",
	font_size	= "h*0.013",
	outline_color  = "white",
	font_color 	= "gray12",
	text_xPosition = "right",
	text_yPosition = "top"
)

################################################################################
##				Calendar Layout setup
################################################################################
## TODO:



################################################################################
##				Weather Layout setup
################################################################################
### WEATHER AREA
weatherData = getWeather()
btnCity = pssm.Button(weatherData["city"]["name"],outline_color  = "white", font_size = "h*0.013",font_color="gray5")
btnToday = pssm.Button("Today",outline_color  = "white",font_size = "h*0.02")
vline = pssm.Line(color="gray10",type="vertical")
hline = pssm.Line(color="gray10",type="horizontal")

# TODAY
h = [Weather_Hour(weatherData,i) for i in range(6)]
layout_weather_today = [
	["?/10", (btnCity,"w/6") , (btnToday,"?") , (None,"w/6")],
	["?", (h[0],"?/6"),(h[1],"?/6"),(h[2],"?/6"),(h[3],"?/6"),(h[4],"?/6"),(h[5],"?/6")]
]
weatherToday = pssm.Layout(layout_weather_today)

# COMING DAYS
d = []
name_dplus1 = "Tomorrow"
name_dplus2 = time.strftime("%A", time.localtime(time.time()+60*60*24*2))
name_dplus3 = time.strftime("%A", time.localtime(time.time()+60*60*24*3))
d.append(Weather_Day(weatherData,1,name_dplus1))
d.append(Weather_Day(weatherData,2,name_dplus2))
d.append(Weather_Day(weatherData,3,name_dplus3))
layout_weather_comingDays = [
	["?", (d[0],"?")],
	[1,(hline,"?")],
	["?", (d[1],"?")],
	[1,(hline,"?")],
	["?", (d[2],"?")]
]
weatherComingDays = pssm.Layout(layout_weather_comingDays)



################################################################################
##				Log Layout setup
################################################################################
## TODO:



################################################################################
##				Main Layout setup
################################################################################
separatorLine = pssm.Line(color="gray10",width=1,type="horizontal")
layout_main = [
	[10																		  ],
	["?/4" , (iconBar, "w*0.2")   , (clock, "?")  ,  (infos, "w*0.15") 		  ],
	[1, 			(separatorLine,"w")										  ],
	["?/4", 			(None,"w")											  ],
	[1,				(separatorLine,"w")										  ],
	["?/4", (weatherToday,"?"),    (vline,1),     (weatherComingDays,"w/3")   ],
	[1, 			(separatorLine,"w")										  ],
	["?/5", 			(None,"w")											  ]
]


################################################################################
##				MAIN LOGIC
################################################################################
#Declare the Screen Stack Manager
screen = pssm.PSSMScreen(device,'Main')
#Start Touch listener, as a separate thread
screen.startListenerThread()
#Clear and refresh the screen
screen.clear()
screen.refresh()
# Then, display it all
main = pssm.Layout(layout_main,screen.area)
screen.addElt(main)

# Then, start the thread which will update the clock every minute
clockThread = threading.Thread(target=setupClock)
clockThread.start()
