# Kobo-Dashboard
A dashboard for Kobo, including a clock, an interactive calendar widget, a weather widget and a phone-notification widget

![Main image](https://github.com/Mavireck/Kobo-Dashboard/blob/master/DemoImages/20190812_145209.jpg?raw=true)


### Installation:
* Install this all-in-one package first (Python, FBInk etc...):
https://www.mobileread.com/forums/showthread.php?t=254214
* Then install KFMon:
https://www.mobileread.com/forums/showthread.php?t=274231
* Then, clone this repository somewhere on your kobo (I recommend /mnt/onboard/.adds/mavireck/Kobo-Dashboard)
* You will need to download the Kobo-Input-Python and Kobo-Python-OSKandUtils repositories.
* Place the folders side by side in /mnt/onboard/.adds/mavireck
* Then add any icon to the root of your onboard storage
* Then, add a config file for KFMon linking the icon you added to the dashboard.sh file from this repo.
* *(take a break)*
* Go to https://openweathermap.org/ and create an account. You will need an APPID. Go find you city ID too.
* Edit the files/config.json file and change screen height, width, the weather appid and city id, and any device-specific data (I only tested it on a Kobo Aura H20 first edition.
* You are ok to go!

### How to use:
* You should start it with wifi on.
* You can turn frontlight up and down with the buttons, and you can also invert the screen.
* To change weeks in the calendar, click on the name of the first and last days being displayed.
* To edit an event, click on the corresponding day, then on the corresponding event. Then, you can change the event data.
* You can update the clock by clicking on it. It will also update the frontlight setting and battery level. Anyway, it is updated every minute (you can change it in the configuration file)
* You can change between Notification mode and Log mode by clicking on the last area. It will start on Log mode by default, and every time a new log is registered, it will go to log mode.

### About the notification mode:
It is meant to be used with your android phone. 
It serves as a secondary notification panel to display all your notification from your phone directly on your Kobo.
I personally use my Kobo as a fancy clock on my desk, and having the notification on the Kobo screen instead allows me to be less distracted by my phone screen.

You need an app which listens to the notification, then sends their content via a HTTP Post request to the kobo. The POST parameters must be "title", "message","package","timestamp". The first 3 must be base64encoded.

I personally use this app:
https://play.google.com/store/apps/details?id=com.llamalab.automate&hl=fr
In the demoImages folder, you will find an image of the flowchart I use. (The Kobo.png file)

Although you can use the one you want. (if you need more details about how I used this app, send me a message via the Mobileread forum)
