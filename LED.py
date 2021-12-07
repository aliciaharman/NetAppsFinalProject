#White: Ready for Query
#Red: User Authentication Failed
#Green: User Authentication Succeeded
#Blue: Performing Query
#Cyan: Completed Query

#http://0.0.0.0::8081/LED?status==xxx:

import sys
import RPi.GPIO as GPIO
import socket
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
GPIO.output(LEDS, False)
global client_ip, client_port, status


def changeLED():
    global status
    if status == 'ready': # white
        GPIO.output(LEDS, (GPIO.HIGH, GPIO.HIGH, GPIO.HIGH))
    elif status == 'failed': # red
        GPIO.output(LEDS, (GPIO.HIGH, GPIO.LOW, GPIO.LOW))
    elif status == 'performing': # blue
        GPIO.output(LEDS, (GPIO.LOW, GPIO.LOW, GPIO.HIGH))
    elif status == 'succeeded': # green
        GPIO.output(LEDS, (GPIO.LOW, GPIO.HIGH, GPIO.LOW))
    elif status == 'completed': # cyan
        GPIO.output(LEDS, (GPIO.LOW, GPIO.HIGH, GPIO.HIGH))
    else:
        GPIO.output(LEDS, False)


def main():
    global client_ip, client_port
    if len(sys.argv) == 5:
        if (sys.argv[1] == '-cip') and (sys.argv[3] == '-cp'):
            client_ip = sys.argv[2]
            client_port = sys.argv[4]


@app.route('/LED', methods=['POST'])
def LED_post():
    global status
    status = request.args.get('status')
    changeLED()
    return "Updated to status: %s." % status


if __name__ == '__main__':
    global client_ip, client_port
    main()
    app.run(host=client_ip, port=client_port, debug=True)
