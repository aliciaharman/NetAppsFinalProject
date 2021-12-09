#White: Ready for Query
#Red: User Authentication Failed
#Green: User Authentication Succeeded
#Blue: Performing Query
#Cyan: Completed Query

#http://0.0.0.0::8081/LED?status==xxx:

import sys
import RPi.GPIO as GPIO
import socket
import time
from flask import Flask, request


app = Flask(__name__)

# Setup GPIO
r = 27
g = 13
b = 26
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
LEDS = (r, g, b)
GPIO.setup(LEDS, GPIO.OUT)
GPIO.output(LEDS, (GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)) # ready; white
global client_ip, status


def changeLED():
    global status
    if status == 'failed': # red
        GPIO.output(LEDS, (GPIO.HIGH, GPIO.LOW, GPIO.LOW))
        time.sleep(2)
        GPIO.output(LEDS, (GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)) # ready; white
    elif status == 'performing': # blue
        GPIO.output(LEDS, (GPIO.LOW, GPIO.LOW, GPIO.HIGH))
    elif status == 'succeeded': # green
        GPIO.output(LEDS, (GPIO.LOW, GPIO.HIGH, GPIO.LOW))
    elif status == 'completed': # cyan
        GPIO.output(LEDS, (GPIO.LOW, GPIO.HIGH, GPIO.HIGH))
        time.sleep(2)
        GPIO.output(LEDS, (GPIO.HIGH, GPIO.HIGH, GPIO.HIGH)) # ready; white


# get the ip address of the current pi
def get_ip():
    global client_ip
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    client_ip = s.getsockname()[0]
    s.close()


# LED flask instance receiving from Cangle Service Pi
@app.route('/LED', methods=['POST'])
def LED_post():
    global status
    status = request.args.get('status')
    changeLED()
    return "Updated to status: %s." % status


if __name__ == '__main__':
    global client_ip
    get_ip()
    app.run(host=client_ip, port=5000, debug=True)