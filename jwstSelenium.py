from Adafruit_IO import Client, Feed
from adafruitKey import LCMKEY, LCMUSERNAME

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

import time
import sys

import pathlib
import os

priorTempsFile = pathlib.Path.home() / 'jwstTemps.txt'

# If there's no historical data, make something up
# NASA only publishes about once per day. The historical data is a csv of
# the readings from the last time this program ran.  I only graph data
# if it changed from the prior execution of this program.
if not priorTempsFile.is_file():
	with priorTempsFile.open( mode='w', encoding='utf-8') as f:
		priorTemps = "0,0,0,0,0,0,0,0,0"
		f.write(priorTemps)
		f.close()
else:
# If there is historical data, read it in
	with priorTempsFile.open( mode='r', encoding="utf-8") as f:
		priorTemps = f.read()
		print(f'Prior temps: {priorTemps}')
		f.close()

# Here are the html names of the sensors
instruments = {
   'tempWarmSide1C'     : 'Sunshield UPS Average Temperature (hot)',
   'tempWarmSide2C'     : 'Spacecraft Equipment Panel Average Temperature (hot)',
   
   'tempCoolSide1C'     : 'Primary Mirror Average Temperature (cold)',
   'tempCoolSide2C'     : 'Instrument Radiator Temperature (cold)',

   'tempInstMiriC'      : 'MIRI Mid InfraRed Instrument',
   'tempInstNirCamC'    : 'NIRCam Near InfraRed Camera',
   'tempInstNirSpecC'   : 'NIRSpec Near InfraRed Spectrometer',
   'tempInstFgsNirissC' : 'FGS/NIRISS Fine Guidance Sensor / Near InfraRed Imager and Slitless Spectrograph',
   'tempInstFsmC'       : 'FSM Fine Steering Mirror'
   }

newReadings = {} # Make a dict of sensor : reading

# Scrape a sensor's value from the web page.
def get_temp_of(sensor):
	try:
		tempResult = wait.until(EC.presence_of_element_located((By.ID, sensor)))
		return tempResult.text
	except:
		print(f'Looking for {sensor}. Exception waiting for temp')
		driver.quit()

# Open the JWST web page.  I'm using Selenium because the page is very dynamic with a lot
# of javascript.  A simple wget or curl shows "--" as the temperatures until the javascript
# executes.
driver = webdriver.Safari()
driver.get("https://www.jwst.nasa.gov/content/webbLaunch/whereIsWebb.html?units=metric")
wait = WebDriverWait(driver,10)

currentTemps = ''

# Get each sensor's current reading
print("Current Temps:")
for index, sensor in enumerate(instruments):
	newReadings[sensor] = get_temp_of(sensor)
	# Build a csv of current temps
	currentTemps = currentTemps + f',{newReadings[sensor]}'
	print(f'{instruments[sensor]}: {newReadings[sensor]}')

# Have any values changed? If so, send them to Adafruit
if currentTemps != priorTemps:
	print("I've detected a temperature change")
	aio = Client(LCMUSERNAME, LCMKEY)
	for index, feed in enumerate(newReadings):
		try:
			if newReadings[feed] != '--': # Check for good data
				print(f'Send {newReadings[feed]} to {feed}')
				aio.send(feed.lower(), newReadings[feed])
			else:
				# Damn, the web page hadn't finished refreshing
				# by the time I started scraping
				print(f'Missing reading for {feed}')
		except:
			print(f'Failure to send {newReadings[feed]} to {feed}') 
else:
	print("There is no change in temperature")

# Write the current temp csv to the history file
if os.path.exists(priorTempsFile):
  os.remove(priorTempsFile)

with priorTempsFile.open( mode='w', encoding='utf-8') as f:
	f.write(currentTemps)
	f.close()

# deprecated close_model = driver.find_element_by_class_name("modal__close")
#close_model = driver.find_element(By.CLASS_NAME, "modal__close")

driver.quit()
