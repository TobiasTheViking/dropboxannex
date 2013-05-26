#!/usr/bin/env python2
import os
import re
import sys
import json
import time
import inspect
import webbrowser

conf = False
version = "0.1.0"
plugin = "dropboxannex-" + version

pwd = os.path.dirname(__file__)
if not pwd:
    pwd = os.getcwd()
sys.path.append(pwd + '/lib')

if "--dbglevel" in sys.argv:
    dbglevel = int(sys.argv[sys.argv.index("--dbglevel") + 1])
else:
    dbglevel = 0

import CommonFunctions as common

import dropbox

app_key = "9pfuayrh738ob9i"
app_secret = "o840cpdu0kxv4u9"
app_type = "dropbox"
import dropbox.client
import dropbox.session
db_sess = dropbox.session.DropboxSession(app_key, app_secret, app_type)
db_client = False

def login():
    common.log("")
    global db_client
    access_token = False
    stored_creds = readFile(pwd + "/dropboxannex.creds")
    if stored_creds:
        try:
            stored_creds = json.loads(stored_creds)
            db_sess.set_token(stored_creds["key"], stored_creds["secret"])
            #access_token = db_sess.obtain_access_token(request_token)
            access_token = True
        except Exception as e:
            common.log("Excpetion: " + repr(e))

    if not access_token:
        request_token = db_sess.obtain_request_token()
        url = db_sess.build_authorize_url(request_token, oauth_callback="http://127.0.0.1/auth_reply/")
        common.log("auth: " + repr(url))
        webbrowser.open(url, True, True)
        print("Please visit this website and press the 'Allow' button, then hit 'Enter' here.")
        key = raw_input()
        common.log("Requesting new access token")
        access_token = db_sess.obtain_access_token(request_token)
        stored_creds = {"key": access_token.key, "secret": access_token.secret}
        common.log("access_token: " + repr(stored_creds))
        saveFile(pwd + "/dropboxannex.creds", json.dumps(stored_creds), "wb")
    

    db_client = dropbox.client.DropboxClient(db_sess)
    common.log("BLA: " + repr(db_client))
    print "linked account:", db_client.account_info()
    common.log("Done: " + repr(db_client))

def postFile(subject, filename, folder):
    common.log("%s to %s - %s" % ( filename, folder[0], subject))
    
    file = findInFolder(subject, folder)
    if file:
        common.log("File already exists: " + repr(file))
        return True

    f = open(filename)
    res = db_client.put_file(folder + subject, f)
    print "uploaded:", res
    if res:
        common.log("Done: " + repr(res))
    else:
        sys.exit(1)

def findInFolder(subject, folder="/"):
    common.log("%s(%s) - %s(%s)" % (repr(subject), type(subject), repr(folder), type(folder)), 0)

    folder_metadata = db_client.metadata(folder)
    
    for file in folder_metadata["contents"]:
        name = file["path"]
        name = name[name.rfind("/") + 1:]
        common.log("folder: " + name + " - " + file["path"], 3)
        if name == subject:
            common.log("Done: " + repr(file))
            return file
    common.log("Failure")

def checkFile(subject, folder):
    common.log(subject)
    global m

    file = findInFolder(subject, folder)
    if file:
        common.log("Found: " + repr(file))
        print(subject)
    else:
        common.log("Failure")

def getFile(subject, filename, folder):
    common.log(subject)
    global m

    file = findInFolder(subject, folder)
    if file:
        common.log("file: " + repr(file))
        f, metadata = db_client.get_file_and_metadata(folder + subject)
        common.log("metadata: " + repr(metadata))
        saveFile(filename, f.read(), "wb")
        common.log("Done")
        return True
    common.log("Failure")


def deleteFile(subject, folder):
    common.log(subject)
    global m

    file = findInFolder(subject, folder)

    if file:
        res = db_client.file_delete(folder + subject)
        if res["is_deleted"]:
            common.log("Done")
            return True
    common.log("Failure")

def readFile(fname, flags="r"):
    common.log(repr(fname) + " - " + repr(flags))

    if not os.path.exists(fname):
        common.log("File doesn't exist")
        return False
    d = ""
    try:
        t = open(fname, flags)
        d = t.read()
        t.close()
    except Exception as e:
        common.log("Exception: " + repr(e), -1)

    common.log("Done")
    return d

def saveFile(fname, content, flags="w"):
    common.log(fname + " - " + str(len(content)) + " - " + repr(flags))
    t = open(fname, flags)
    t.write(content)
    t.close()
    common.log("Done")

def createFolder(path):
    common.log(path)
    res = db_client.file_create_folder(path)
    common.log(res)
    return path

def main():
    global conf
    args = sys.argv

    ANNEX_ACTION = os.getenv("ANNEX_ACTION")
    ANNEX_KEY = os.getenv("ANNEX_KEY")
    ANNEX_HASH_1 = os.getenv("ANNEX_HASH_1")
    ANNEX_HASH_2 = os.getenv("ANNEX_HASH_2")
    ANNEX_FILE = os.getenv("ANNEX_FILE")
    envargs = []
    if ANNEX_ACTION:
        envargs += ["ANNEX_ACTION=" + ANNEX_ACTION]
    if ANNEX_KEY:
        envargs += ["ANNEX_KEY=" + ANNEX_KEY]
    if ANNEX_HASH_1:
        envargs += ["ANNEX_HASH_1=" + ANNEX_HASH_1]
    if ANNEX_HASH_2:
        envargs += ["ANNEX_HASH_2=" + ANNEX_HASH_2]
    if ANNEX_FILE:
        envargs += ["ANNEX_FILE=" + ANNEX_FILE]
    common.log("ARGS: " + repr(" ".join(envargs + args)))

    if not os.path.exists(pwd + "/dropboxannex.conf"):
        saveFile(pwd + "/dropboxannex.conf", json.dumps({"folder": "gitannex"}))
        common.log("no dropboxannex.conf file found. Creating empty template")
        sys.exit(1)

    conf = readFile(pwd + "/dropboxannex.conf")
    try:
        conf = json.loads(conf)
    except Exception as e:
        common.log("Traceback EXCEPTION: " + repr(e))
        common.log("Couldn't parse conf: " + repr(conf))
        conf = {}

    common.log("Conf: " + repr(conf), 2)

    login()
    
    folder = findInFolder(conf["folder"])
    if folder:
        common.log("Using folder: " + repr(folder))
        ANNEX_FOLDER = folder["path"]  + "/"
    else:
        folder = createFolder("/" + conf["folder"])
        common.log("created folder0: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    folder = findInFolder(ANNEX_HASH_1, ANNEX_FOLDER)
    if folder:
        common.log("Using folder1: " + repr(folder))
        ANNEX_FOLDER = folder["path"] + "/"
    else:
        folder = createFolder(ANNEX_FOLDER + "/" + ANNEX_HASH_1)
        common.log("created folder1: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    folder = findInFolder(ANNEX_HASH_2, ANNEX_FOLDER)
    if folder:
        common.log("Using folder2: " + repr(folder))
        ANNEX_FOLDER = folder["path"] + "/"
    else:
        folder = createFolder(ANNEX_FOLDER + "/" + ANNEX_HASH_2)
        common.log("created folder2: " + repr(folder))
        ANNEX_FOLDER = folder + "/"

    if "store" == ANNEX_ACTION:
        postFile(ANNEX_KEY, ANNEX_FILE, ANNEX_FOLDER)
    elif "checkpresent" == ANNEX_ACTION:
        checkFile(ANNEX_KEY, ANNEX_FOLDER)
    elif "retrieve" == ANNEX_ACTION:
        getFile(ANNEX_KEY, ANNEX_FILE, ANNEX_FOLDER)
    elif "remove" == ANNEX_ACTION:
        deleteFile(ANNEX_KEY, ANNEX_FOLDER)
    else:
        common.log("ERROR")
        sys.exit(1)

t = time.time()
common.log("START")
if __name__ == '__main__':
    main()
common.log("STOP: %ss" % int(time.time() - t))
