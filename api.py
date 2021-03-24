# teahaz.py : api interface for teahaz-server for bots and messaging clients
# Copyright (C) 2021  thomasthethermonuclearbomb@tutanota.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
import os
import string
import base64

# placeholder for ecryption function
# WARNING: while you can call these functions directly, it is not recomended as they might change in different versions
def encrypt_message(a):
    return base64.b64encode(str(a).encode('utf-8')).decode('utf-8')


# placeholder for ecryption function
# WARNING: while you can call these functions directly, it is not recomended as they might change in different versions
def encrypt_binary(a):
    return base64.b64encode(a).decode('utf-8')



# placeholder for decryption function
# WARNING: while you can call these functions directly, it is not recomended as they might change in different versions
def decrypt_message(a):
    return base64.b64decode(str(a).encode('utf-8')).decode('utf-8')


# placeholder for decryption function
# WARNING: while you can call these functions directly, it is not recomended as they might change in different versions
def decrypt_binary(a):
    return base64.b64decode(str(a).encode('utf-8'))



def sanitize_filename(a):
    allowed = string.ascii_letters + string.digits + '_-.'
    a = a.replace('..', '_')

    filename = ''
    for i in a:
        if i not in allowed:
            i = '_'
        filename += i

    return filename



# upload a file using the v0 api
def upload_file_v0(session, base_url, chatroomId, username, filepath, filename):
    url = base_url + '/api/v0/file/' + chatroomId

    # mnake sure there arent any wierd chars in the filename
    filename = sanitize_filename(filename)

    # get the length of the file
    f = open(filepath, 'ab+')
    length = f.tell()
    f.close()



    # the User-Agent header is set so we can easily identify outdated/insecure versions
    headers = {
            "User-Agent": "teahaz.py (v0.1 alpha)"
            }


    # open file in read binary mode
    f = open(filepath, 'rb')


    # chunksize supported by the server is one megabyte.
    # the equasion represents how the chunk_size will grow due to encryption, and -1 is there to fix rounding issues
    chunk_size = int((1048576*3)/4) -1

    # part will be set to false when we have sent the end of the file
    part = True
    fileId = None
    while part:
        c = f.read(chunk_size)

        # check if this will be the last part
        if len(c) < chunk_size or f.tell() >= length :
            part = False


        # set up needed json
        json = {
            "type": 'file',
            "username": username,
            "chatroom": chatroomId,
            'filename': filename,
            'fileId'  : fileId,
            'part'    : part,
            'data'    : encrypt_binary(c)
                }


        # make request
        response = session.post(url, json=json, headers=headers)
        if response.status_code != 200:
            break
        else:
            fileId = response.text.strip(' ').strip('\n').strip('"')


    f.close()
    # return the response if the loop stopped
    return response.text, response.status_code



# download a file using the v0 api
# WARNING: you must sanitize filenames before pasing to this function as it doesnt know the basename
def download_file_v0(session, base_url, chatroomId, username, fileId, save_as):
    url = base_url + '/api/v0/file/' + chatroomId


    # the file uses append, so It has to remove the file if it already exists
    if os.path.exists(save_as):
        os.remove(save_as)

    # file section to get
    # section starts with 1 because section 0 is the owner of the file
    section = 1
    while True:

        # set headers
        # the User-Agent header is set so we can easily identify outdated/insecure versions
        headers = {
                "User-Agent": "teahaz.py (v0.1 alpha)",

                "username": username,
                "fileId"  : fileId,
                "section" : str(section)
                }


        response = session.get(url, headers=headers)
        # let the programmer handle errors
        if response.status_code != 200:
            return response.text, response.status_code


        # try decode data
        try:
            data = decrypt_binary(response.text.strip(' ').strip('\n').strip('"'))
        except Exception as e:
            return f"ERR: could not decrypt file data. Traceback: {e}", 500


        if len(data) < 1:
            break

        # write the data to file
        with open(save_as, "ab+")as outfile:
            outfile.write(data)

        section += 1



    return "OK", 200



# create an invite for a given chatroom
def create_invite_v0(session, base_url, chatroomId, username, expiration_time_epoch, uses):
    url = base_url + '/api/v0/invite/' + chatroomId


    # the User-Agent header is set so we can easily identify outdated/insecure versions
    # setup headers
    json = {
            "User-Agent": "teahaz.py (v0.1 alpha)",

            "username": username,
            "expr-time": str(expiration_time_epoch),
            "uses": str(uses)
            }


    # make request
    res = session.get(url=url, headers=json)
    return res.text, res.status_code

