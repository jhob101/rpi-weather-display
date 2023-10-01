# Display Weather Data from adafruit.io on InkyPHat eInk display

## Installation
Copy `env.example` to `.env` and fill in the values.

Install the required python packages:

`pip3 install python-dotenv`

and some others... but make sure it's that dotenv library that gets installed.  There's a few similarly name libraries.

## Set up cron job
`crontab -e`

Add the following line to the end of the file:

`*/5 * * * * python3 /home/pi/Python_Code/Weather_Display/weather-display.py --colour "red"`
