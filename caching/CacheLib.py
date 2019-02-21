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

    def get(self, filename, encryption, dirToSave):
        # make request to cache server
        try:
            req = requests.get("http://"+self.cacheServerAddress+"/get/"+encryption+"/"+filename)
        except requests.exceptions.RequestException as error:
            print "Error making request to cache server: "+str(error)
            return -1

        if not req.ok:
            print "Error getting response from cache: "+str(req.text)

        # validate directory
        dirToSave = CacheUtils.validateDirectory(dirToSave)
        if dirToSave == -1:
            return -1

        # save cached file to specified directory
        try:
            with open(dirToSave+filename, "wb") as f:
                f.write(req.content)
        except IOError as error:
            print "Error saving cached file: "+str(error)
            return -1

        return 0

    def put(self, filepath, encryption):
        # open file to be put
        try:
            with open(filepath, "rb") as f:
                fileContents = f.read()
        except IOError as error:
            print "Could not open file at path "+filepath+": "+str(error)
            return -1

        # get filename from path
        filename = filepath.split("/")[-1]

        # make request to cache server
        try:
            req = requests.put("http://"+self.cacheServerAddress+"/put/"+encryption, data=fileContents)
        except requests.exceptions.RequestException as error:
            print "Error making request to cache server: "+str(error)
            return -1

        if req.ok:
            newFilename = req.content
            print "PUT sucessful"
        else:
            print "Error putting file in cache server: "+str(req.text)
            return -1

        return newFilename