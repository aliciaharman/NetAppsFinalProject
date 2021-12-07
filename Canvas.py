# Network Application | Final Project
from flask import Flask, request, render_template
from flask_httpauth import HTTPBasicAuth
from pymongo import MongoClient
import requests
import json
import servicesKeys as service
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import sys


app = Flask(__name__)
auth = HTTPBasicAuth()
header = requests.structures.CaseInsensitiveDict()
header["Authorization"] = 'Bearer ' + str(service.canvas_tok)
user_id = '100667'
global client_ip, client_port, status
client_url = 'http://%s:%s/LED?status=%s' %(client_ip, client_port, status)

def client_info():
    global client_ip, client_port
    if (sys.argv[1] == '-cip') and (sys.argv[3] == '-cp'):
        client_ip = sys.argv[2]
        client_port = int(sys.argv[4])

def get_course_id(name):
    course_parm = requests.structures.CaseInsensitiveDict()
    course_parm['enrollment_state'] = 'active'
    course_parm['per_page'] = '100'
    course_url = 'https://vt.instructure.com/api/v1/courses?'
    r = requests.get(url=course_url, headers=header, params=course_parm)
    # format text returned
    course_dic = json.loads(r.text)
    for i in range(len(course_dic)):
        if course_dic[i]['name'] == name:
            return course_dic[i]['id']
    return "404 Not Found"


def integrate_one(event_name, course, type):
    cal_parm = requests.structures.CaseInsensitiveDict()
    cal_parm['all_events'] = '1'
    if course != None:
        cal_parm['context_codes[]'] = 'course_%s' %(course)
    cal_parm['type'] = type
    calendar_url = 'https://vt.instructure.com/api/v1/calendar_events'
    r = requests.get(url=calendar_url, headers=header, params=cal_parm)
    # format text returned
    events_dic = json.loads(r.text)
    start = []
    end = []
    # go through the list of dictionaries to get special id & title
    for i in range(len(events_dic)):
        if events_dic[i]['title'] == event_name:
            if type == 'event':
                start.append(events_dic[i]['start_at'])
                end.append(events_dic[i]['end_at'])
            else:
                start.append(events_dic[i]['assignment']['unlock_at'])
                end.append(events_dic[i]['assignment']['due_at'])
    return [event_name], start, end


# Utilize Canvas APi to get all relevant event information; return info in json format
def integrate_all(course, type):
    cal_parm = requests.structures.CaseInsensitiveDict()
    cal_parm['all_events'] = '1'
    if course != None:
        cal_parm['context_codes[]'] = 'course_%s' %(course)
    cal_parm['type'] = type
    calendar_url = 'https://vt.instructure.com/api/v1/calendar_events'
    r = requests.get(url=calendar_url, headers=header, params=cal_parm)
    event_title = []
    start_at = []
    end_at = []
    # format text returned
    events_dic = json.loads(r.text)
    # go through the list of dictionaries to get special id & title
    for i in range(len(events_dic)):
        if type == 'event':
            event_title.append(events_dic[i]['title'])
            start_at.append(events_dic[i]['start_at'])
            end_at.append(events_dic[i]['end_at'])
        else:
            event_title.append(events_dic[i]['title'])
            end_at.append(events_dic[i]['assignment']['due_at'])
            start_at.append(events_dic[i]['assignment']['unlock_at'])
    return event_title, start_at, end_at


def integrate_win(course, start, end, type):
    cal_parm = requests.structures.CaseInsensitiveDict()
    if course != None:
        cal_parm['context_codes[]'] = 'course_%s' %(course)
    cal_parm['start_date'] = start
    cal_parm['end_date'] = end
    cal_parm['type'] = type
    calendar_url = 'https://vt.instructure.com/api/v1/calendar_events'
    r = requests.get(url=calendar_url, headers=header, params=cal_parm)
    event_title = []
    start_at = []
    end_at = []
    # format text returned
    events_dic = json.loads(r.text)
    # go through the list of dictionaries to get special id & title
    for i in range(len(events_dic)):
        if type == 'event':
            event_title.append(events_dic[i]['title'])
            start_at.append(events_dic[i]['start_at'])
            end_at.append(events_dic[i]['end_at'])
        else:
            event_title.append(events_dic[i]['title'])
            end_at.append(events_dic[i]['assignment']['due_at'])
            start_at.append(events_dic[i]['assignment']['unlock_at'])
    return event_title, start_at, end_at


def create_event(title, start, end):
    cal_parm = requests.structures.CaseInsensitiveDict()
    cal_parm['calendar_event[context_code]'] = 'User_%s' %(user_id)
    cal_parm['calendar_event[title]'] = title
    cal_parm['calendar_event[start_at]'] = start
    cal_parm['calendar_event[end_at]'] = end
    calendar_url = 'https://vt.instructure.com/api/v1/calendar_events.json'
    r = requests.post(url=calendar_url, headers=header, data=cal_parm)



def google_api(name, start, end):
    creds = None
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
    services = build('calendar', 'v3', credentials=creds)

    for x in range(len(name)):
        event = {
            'summary' : name[x],
            'start' : {
                'dateTime' : start[x],
                'timeZone' : 'UTC',
            },
            'end' : {
                'dateTime' : end[x],
                'timeZone' : 'UTC',
            },
        }
        event = services.events().insert(calendarId='primary', body=event).execute()
        print('Event created')


# authenticate user
@auth.verify_password
def verify_password(username, password):
    global client_ip, client_port, status
    client = MongoClient('localhost', 27017)
    db = client["Cangle"]
    collection = db["service_auth"]
    user_entry = {"username":str(username), "password":str(password)}
    doc = collection.find(user_entry) # locate query in database
    # validate and check cursor entry within the database for authentication
    if doc == None:
        status = 'failed'
        doc.close() # delete and reallocate cursor resource
        requests.post(url=client_url)
        return False
    else:
        for x in doc:
            user = x["username"]
            secret = x["password"]
            doc.close() # delete and reallocate cursor resource
            if (user == username) and (secret == password):
                status = 'succeeded'
                requests.post(url=client_url)
                return True
            else:
                status = 'failed'
                requests.post(url=client_url)
                return False


# Authentication Error Handler
@auth.error_handler
def auth_error(status):
    return "Access Denied Invalid Username or Password. ", status


@app.route('/Cangle/<query>', methods=['GET'])
def manual(query):
    global client_ip, client_port, status
    status = 'performing'
    requests.post(url=client_url)
    if query == 'manual':
        status = 'completed'
        requests.post(url=client_url)
        return render_template('Cangle_manual.html')
    else:
        status = 'completed'
        requests.post(url=client_url)
        return '404 error: ', query, ' file not found'


@app.route('/Cangle', methods=['GET', 'POST'])
@auth.login_required
def canvas_google():
    global client_ip, client_port, status
    status = 'performing'
    requests.post(url=client_url)
    command = request.args.get('command')
    if request.method == 'GET':
        if command == 'course_id':
            name = request.args.get('course_name')
            course = get_course_id(name)
            status = 'completed'
            requests.post(url=client_url)
            return 'Course ID: ' + str(course)
        elif command == 'integrate':
            course_id = request.args.get('course_id')
            all_events = request.args.get('all_events')
            type = request.args.get('type')
            if type == None:
                type = 'assignment'
            if all_events != None:
                name, start, end = integrate_all(course_id, type)
                if len(name) != 0:
                    google_api(name, start, end)
                    status = 'completed'
                    requests.post(url=client_url)
                    return "Events Have Been Added. Reload Google Calendar to confirm."
                else:
                    status = 'completed'
                    requests.post(url=client_url)
                    return "No assignment/event(s) found. Please try again."
            else:
                start = request.args.get('start')
                end = request.args.get('end')
                event_name = request.args.get('event_name')
                if event_name != None:
                    name, start, end = integrate_one(event_name, course_id, type)
                    if len(start) != 0:
                        google_api(name, start, end)
                        status = 'completed'
                        requests.post(url=client_url)
                        return "%s Have Been Added" %event_name
                    else:
                        status = 'completed'
                        requests.post(url=client_url)
                        return "Unable to find assignment/event. Please try again."
                else:
                    if (start == None) | (end == None):
                        status = 'completed'
                        requests.post(url=client_url)
                        return "Invalid Entry: Check Field Name and Values."
                    else:
                        name, start, end = integrate_win(course_id, start, end, type)
                        if len(name) != 0:
                            google_api(name, start, end)
                            status = 'completed'
                            requests.post(url=client_url)
                            return "Window of Events Have Been Added"
                        else:
                            status = 'completed'
                            requests.post(url=client_url)
                            return "No assignment/event(s) found. Please try again."

    if request.method == 'POST':
        if command == 'create':
            event_name = request.args.get('event_name')
            start = request.args.get('start')
            end = request.args.get('end')
            if ((event_name, start, end) != None):
                create_event(event_name, start, end)
                google_api(event_name, start, end)
                status = 'completed'
                requests.post(url=client_url)
                return "Event has been added."
            else:
                status = 'completed'
                requests.post(url=client_url)
                return "Invalid: Missing a Field."


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    client_info()
    app.run(host='0.0.0.0', port=8081, debug=True)
