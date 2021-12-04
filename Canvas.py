# Network Application | Final Project
from flask import Flask, request, render_template
from flask_httpauth import HTTPBasicAuth
from pymongo import MongoClient
import requests
import json
import servicesKeys as service


app = Flask(__name__)
auth = HTTPBasicAuth()
get_header = requests.structures.CaseInsensitiveDict()
get_header["Authorization"] = 'Bearer ' + str(service.canvas_tok)

def get_course_id(name):
    course_parm = requests.structures.CaseInsensitiveDict()
    course_parm['enrollment_state'] = 'active'
    course_parm['per_page'] = '100'
    course_url = 'https://vt.instructure.com/api/v1/courses?'
    r = requests.get(url=course_url, headers=get_header, params=course_parm)
    # format text returned
    course_dic = json.loads(r.text)
    for i in range(len(course_dic)):
        if course_dic[i]['name'] == name:
            return course_dic[i]['id']
    return "404 Not Found"


def integrate_one(event_name):
    pass


# Utilize Canvas APi to get all relevant event information; return info in json format
def integrate_all(course, type):
    cal_parm = requests.structures.CaseInsensitiveDict()
    cal_parm['all_events'] = '1'
    cal_parm['context_codes[]'] = 'course_%s' %(course)
    cal_parm['type'] = type
    calendar_url = 'https://vt.instructure.com/api/v1/calendar_events'
    r = requests.get(url=calendar_url, headers=get_header, params=cal_parm)
    event_id = []
    event_title = []
    start_at = []
    end_at = []
    location = []
    # format text returned
    events_dic = json.loads(r.text)
    # go through the list of dictionaries to get special id & title
    for i in range(len(events_dic)):
        if type == 'event':
            event_id.append(events_dic[i]['id'])
            event_title.append(events_dic[i]['title'])
            start_at.append(events_dic[i]['start_at'])
            end_at.append(events_dic[i]['end_at'])
            location.append(events_dic[i]['location_name'])
        else:
            event_title.append(events_dic[i]['title'])
            event_id.append(events_dic[i]['assignment']['id'])
    if type == 'assignment':
        assignment_field = ['assignment_ids[]'] * len(event_id)
        assignment_id = list(zip(assignment_field, event_id))
        print(assignment_id)
        assignment_url = 'https://vt.instructure.com/api/v1/courses/%s/assignments' %(course)
        r = requests.get(url=assignment_url, headers=get_header, params=assignment_id)
        due = []
        # convert string to dictionary
        assignments = json.loads(r.text)
        for i in range(len(assignments)):
            due.append(assignments[i]["due_at"])
    # place info gathered into json form for google api
    return events_dic


def integrate_win(course, start, end):
    pass


# authenticate user
@auth.verify_password
def verify_password(username, password):
    client = MongoClient('localhost', 27017)
    db = client["Cangle"]
    collection = db["service_auth"]
    user_entry = {"username":str(username), "password":str(password)}
    doc = collection.find(user_entry) # locate query in database
    # validate and check cursor entry within the database for authentication
    if doc == None:
        doc.close() # delete and reallocate cursor resource
        return False
    else:
        for x in doc:
            user = x["username"]
            secret = x["password"]
            doc.close() # delete and reallocate cursor resource
            return (user == username) and (secret == password)


# Authentication Error Handler
@auth.error_handler
def auth_error(status):
    return "Access Denied Invalid Username or Password. ", status


@app.route('/Cangle/<query>', methods=['GET'])
def manual(query):
    if query == 'manual':
        return render_template('Cangle_manual.html')
    else:
        return '404 error: ', query, ' file not found'


@app.route('/Cangle', methods=['GET', 'POST'])
def canvas_google():
    command = request.args.get('command')
    if request.method == 'GET':
        if command == 'course_id':
            name = request.args.get('course_name')
            course = get_course_id(name)
            return 'Course ID: ' + str(course)
        elif command == 'integrate_all':
            course_id = request.args.get('course_id')
            all_events = request.args.get('all_events')
            type = request.args.get('type')
            if type == None:
                type = 'assignment'
            if all_events:
                hi = integrate_all(course_id, type)
            else:
                start = request.args.get('start')
                end = request.args.get('end')
                event_name = request.args.get('event_name')
                if event_name == None:
                    pass
                else:
                    pass

    if request.method == 'POST':
        if command == 'create':
            pass


    # if request.method == 'POST':


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
