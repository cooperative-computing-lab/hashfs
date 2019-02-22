import requests
import json
import os
import base64
import CacheUtils

class CacheLib:

    def __init__(self, address):
        if address[-1] == "/":
            address = address[:-1]
        self.cacheServerAddress = address

    def get(self, filename, encryption, dirToSave, verbose=False):
        # make request to cache server
        try:
            req = requests.get("http://"+self.cacheServerAddress+"/get/"+encryption+"/"+filename)
        except requests.exceptions.RequestException as error:
            print "Error making GET request to cache server: "+str(error)
            return -1

        if not req.ok:
            if req.status_code == 404:
                print "GET Error, no such file in cache server: "+filename
            else:
                print "Error making GET request to cache server"
            if verbose:
                print req.text
            return -1

        # validate directory
        dirToSave = CacheUtils.validateDirectory(dirToSave)
        if dirToSave == -1:
            return -1 # error printed out in validateDirectory

        # save cached file to specified directory
        try:
            with open(dirToSave+filename, "wb") as f:
                f.write(req.content)
        except IOError as error:
            print "Error saving cached file: "+str(error)
            return -1

        if verbose:
            print "GET successful, file saved to "+dirToSave+filename

        return 0

    def put(self, filepath, encryption, verbose=False):
        # open file to be put
        try:
            with open(filepath, "rb") as f:
                fileContents = f.read()
        except IOError as error:
            print "PUT error: "+str(error)
            return -1

        # make request to cache server
        try:
            req = requests.put("http://"+self.cacheServerAddress+"/put/"+encryption, data=fileContents)
        except requests.exceptions.RequestException as error:
            print "Error making PUT request to cache server: "+str(error)
            return -1

        # check if request succeeded
        if not req.ok:
            print "Error putting file in cache server"
            if verbose:
                print req.text
            return -1

        newFilename = req.content
        if verbose:
            print "PUT successful, new file name: "+str(newFilename)
        return str(newFilename)

    def push(self, filename, encryption, verbose=False):
        # make request to cache server
        try:
            req = requests.put("http://"+self.cacheServerAddress+"/push/"+encryption+"/"+filename)
        except requests.exceptions.RequestException as error:
            print "Error making PUSH request to cache server: "+str(error)
            return -1

        # check if request succeeded
        if not req.ok:
            if req.status_code == 404:
                print "PUSH Error, no such file in cache server: "+str(filename)
            else:
                print "Error during PUSH to cache server"
            if verbose:
                print req.text
            return -1

        if verbose:
            print "PUSH successful"
        return 0

    def info(self, filename, encryption, verbose=False):
        # make request to cache server
        try:
            req = requests.get("http://"+self.cacheServerAddress+"/info/"+encryption+"/"+filename)
        except requests.exceptions.RequestException as error:
            print "Error making INFO request to cache server: "+str(error)
            return -1

        # check if request succeeded
        if not req.ok:
            if req.status_code == 404:
                print "INFO Error, no such file in cache server: "+str(filename)
            else:
                print "Error getting file info"
            if verbose:
                print req.text
            return -1

        # return file info as dict
        try:
            jsonFileInfo = json.loads(req.text)
        except:
            print "Error decoding json response"
            return -1

        if verbose:
            print "Got file info successfully"
        return jsonFileInfo