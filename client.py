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


# FUNCTIONS
## SENDING METHOD
def send(message,mType='text'):
    # base data array, added onto later
    data = {
        "username": USERNAME,
        "cookie": COOKIE,
        "chatroom": ROOMID,
    }

    if mType = 'text':
        # add text-specific fields to data
        data += {
                "message": encode(message),
                'type': "text"
        }

    elif mType = 'file':
        # get file contents
        with open(message, 'rb') as infile:
            contents = encode_binary(infile.read())

        # get file extension bc mimetype sucks sometimes
        extension = message.split(".")[-1]

        data += {
            'type': "file"
            'extension': extension,
            'data': contents
        }

    else:
        return "Error: Invalid message type '"+str(mType)+"'"

    res = s.post(url=url, json=data)

    return res.text



