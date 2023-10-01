#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv
import time
import datetime
from datetime import date
from Adafruit_IO import Client, Feed, Data, Dashboard, RequestError
import glob
import os
from sys import exit

from font_fredoka_one import FredokaOne
from inky.auto import auto
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

try:
    import geocoder
except ImportError:
    exit("This script requires the geocoder module\nInstall with: sudo pip install geocoder")

try:
    from bs4 import BeautifulSoup
except ImportError:
    exit("This script requires the bs4 module\nInstall with: sudo pip install beautifulsoup4==4.6.3")

print("""Weather Report
        """)
        
# Get the current path
PATH = os.path.dirname(__file__)

# Set up the display
try:
    inky_display = auto(ask_user=True, verbose=True)
except TypeError:
    raise TypeError("You need to update the Inky library to >= v1.1.0")

if inky_display.resolution not in ((212, 104), (250, 122)):
    w, h = inky_display.resolution
    raise RuntimeError("This example does not support {}x{}".format(w, h))

inky_display.set_border(inky_display.BLACK)

# Details to customise your weather display
CITY = os.getenv("CITY")
COUNTRYCODE = os.getenv("COUNTRYCODE")
WARNING_TEMP = float(os.getenv("WARNING_TEMP"))


# Convert a city name and country code to latitude and longitude
def get_coords(address):
    g = geocoder.arcgis(address)
    coords = g.latlng
    return coords


# Query Dark Sky (https://darksky.net/) to scrape current weather data
def get_weather(address):
    coords = get_coords(address)
    weather = {}
    res = requests.get("https://darksky.net/forecast/{}/uk212/en".format(",".join([str(c) for c in coords])))
    if res.status_code == 200:
        soup = BeautifulSoup(res.content, "lxml")
        curr = soup.find_all("span", "currently")
        weather['summary']='';
        #weather["summary"] = curr[0].img["alt"].split()[0]
        #weather["temperature"] = int(curr[0].find("span", "summary").text.split()[0][:-1])
        #press = soup.find_all("div", "pressure")
        #weather["pressure"] = int(press[0].find("span", "num").text)

    # Get the current weather from Adafruit IO
    ADAFRUIT_IO_KEY = os.getenv("ADAFRUIT_IO_KEY")
    ADAFRUIT_IO_USERNAME = os.getenv("ADAFRUIT_IO_USERNAME")

    aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

    weather["temperature"] = int(float(aio.receive('temperature').value))
    weather["pressure"] = int(float(aio.receive('pressure').value))
    weather["humidity"] = int(float(aio.receive('humidity').value))
    print('{}*C {}hPa {}%'.format(weather["temperature"], weather["pressure"], weather["humidity"]))

    return weather
        
def create_mask(source, mask=(inky_display.WHITE, inky_display.BLACK, inky_display.RED)):
    """Create a transparency mask.

    Takes a paletized source image and converts it into a mask
    permitting all the colours supported by Inky pHAT (0, 1, 2)
    or an optional list of allowed colours.

    :param mask: Optional list of Inky pHAT colours to allow.

    """
    mask_image = Image.new("1", source.size)
    w, h = source.size
    for x in range(w):
        for y in range(h):
            p = source.getpixel((x, y))
            if p in mask:
                mask_image.putpixel((x, y), 255)

    return mask_image


# Dictionaries to store our icons and icon masks in
icons = {}
masks = {}

# Get the weather data for the given location
location_string = "{city}, {countrycode}".format(city=CITY, countrycode=COUNTRYCODE)
weather = get_weather(location_string)

# This maps the weather summary from Dark Sky
# to the appropriate weather icons
icon_map = {
    "snow": ["snow", "sleet"],
    "rain": ["rain"],
    "cloud": ["fog", "cloudy", "partly-cloudy-day", "partly-cloudy-night"],
    "sun": ["clear-day", "clear-night"],
    "storm": [],
    "wind": ["wind"]
}

# Placeholder variables
pressure = 0
temperature = 0
weather_icon = None

if weather:
    temperature = weather["temperature"]
    pressure = weather["pressure"]
    humidity = weather["humidity"]
    summary = weather["summary"]

    for icon in icon_map:
        if summary in icon_map[icon]:
            weather_icon = icon
            break

else:
    print("Warning, no weather information found!")

# Create a new canvas to draw on
img = Image.open(os.path.join(PATH, "resources/backdrop.png")).resize(inky_display.resolution)
draw = ImageDraw.Draw(img)

# Load our icon files and generate masks
for icon in glob.glob(os.path.join(PATH, "resources/icon-*.png")):
    icon_name = icon.split("icon-")[1].replace(".png", "")
    icon_image = Image.open(icon)
    icons[icon_name] = icon_image
    masks[icon_name] = create_mask(icon_image)

# Load the FredokaOne font
font = ImageFont.truetype(FredokaOne, 60)
font_sml = ImageFont.truetype(FredokaOne, 22)
font_tiny = ImageFont.truetype(FredokaOne, 14)

# Draw lines to frame the weather data
#draw.line((69, 36, 69, 81))       # Vertical line
#draw.line((31, 35, 184, 35))      # Horizontal top line
#draw.line((69, 58, 174, 58))      # Horizontal middle line
draw.line((169, 58, 169, 58), 2)  # Red seaweed pixel :D

# Write text with weather values to the canvas
date_now = time.strftime("%d/%m")
time_now = time.strftime("%H:%M")

#draw.text((36, 12), datetime, inky_display.WHITE, font=font)
draw.text((64, 6), u"{}°".format(temperature), inky_display.WHITE if temperature < WARNING_TEMP else inky_display.RED, font=font)

draw.text((170, 20), date_now, inky_display.WHITE, font=font_tiny)
draw.text((155, 36), time_now, inky_display.WHITE, font=font_sml)

draw.text((64, 69), "{}".format(pressure), inky_display.WHITE, font=font_sml)
draw.text((102, 77), "hPa", inky_display.WHITE, font=font_tiny)

draw.text((135, 69), "{}%".format(humidity), inky_display.WHITE, font=font_sml)

# Draw the current weather icon over the backdrop
if weather_icon is not None:
    img.paste(icons[weather_icon], (28, 36), masks[weather_icon])

else:
    draw.text((28, 36), "?", inky_display.RED, font=font)

# Display the weather data on Inky pHAT
inky_display.set_image(img)
inky_display.show()
