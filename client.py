# CHECK NOTES
# IMPORTS
import requests
import json
import base64


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


# FILE SENDING METHOD
def send_file(f=None):
    # get filename
    ## TODO: add file selector UI
    if f == None:
        return
    
    # use given
    else:
        filename = f

    # get file contents
    with open(filename, 'rb')as infile:
        contents = encode_binary(infile.read())

    # get file extension bc mimetype sucks sometimes
    extension = filename.split(".")[-1]

    data = {
        "username": USERNAME,
        "cookie": COOKIE,
        "chatroom": ROOMID,
        "type": 'file',
        'extension': extension,
        'data': contents
    }

    res = s.post(url=url, json=data)

    return res.text



