# IMPORTS
import os
import json
import base64
import requests


# HELPERS
def encode(a):
    return base64.b64encode(a.encode('utf-8')).decode('utf-8')
def encode_binary(a):
    return base64.b64encode(a).decode('utf-8')


# GLOBALS
URL = "http://localhost:5000/api/v0/"
SESSION = requests.Session()
ROOMID = "conv1"
USERNAME = "me"
COOKIE = "test_cookie"

# base data array, added onto later
BASE_DATA = {
    "username": USERNAME,
    "cookie": COOKIE,
    "chatroom": ROOMID,
}


# FUNCTIONS
## RECEIVING METHOD
def get(time):
    # set specific fields
    endpoint = "message"
    data = BASE_DATA + { 'time': str(time) } 

    # get response
    response = requests.get(url=URL+endpoint,headers=BASE_DATA)
    return response.text

## SENDING METHOD
def send(message,mType='text'):
    # base data gets appended to
    data = BASE_DATA
    
    # handle specificities
    if mType = 'text':
        # set text-specific fields
        data += {
                "message": encode(message),
                'type': "text"
        }
        endpoint = "message"

    elif mType = 'file':
        # get file contents
        with open(message, 'rb') as infile:
            contents = encode_binary(infile.read())

        # get file extension bc mimetype sucks sometimes
        extension = message.split(".")[-1]

        # set file-specific fields
        data += {
            'type': "file"
            'extension': extension,
            'data': contents
        }
        endpoint = "file"

    else:
        return "Error: Invalid message type '"+str(mType)+"'"

    # return response
    response = s.post(url=URL+endpoint, json=data)
    return response.text



