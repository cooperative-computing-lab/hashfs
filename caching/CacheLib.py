import requests
import json
import os
import ast
import CacheUtils
from CacheUtils import getErrorMessageFromServerResponse

class FileNotFound(Exception):
    pass

class InternalServerError(Exception):
    pass

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
            raise InternalServerError("Error making GET request to cache server: "+str(error))

        if not req.ok:
            if req.status_code == 404:
                raise FileNotFound("GET Error, no such file in cache server: "+str(filename))
            else:
                raise InternalServerError(getErrorMessageFromServerResponse(req.text))

        # validate directory
        dirToSave = CacheUtils.validateDirectory(dirToSave)
        if dirToSave == -1:
            raise InternalServerError("Error creating directory: "+str(dirToSave))

        # save cached file to specified directory
        try:
            with open(dirToSave+filename, "wb") as f:
                f.write(req.content)
        except IOError as error:
            raise InternalServerError("Error saving cached file: "+str(error))

        return 0

    def put(self, filepaths, encryption):
        if type(filepaths) is not list:
            filepaths = [filepaths]

        # build files arrays
        filesArray = []
        for fpath in filepaths:
            try:
                filesArray.append(('file', open(fpath, "rb")))
            except IOError as error:
                raise InternalServerError("PUT error: "+str(error))

        # make request to cache server
        try:
            req = requests.put("http://"+self.cacheServerAddress+"/put/"+encryption, files=filesArray)
        except requests.exceptions.RequestException as error:
            raise InternalServerError("Error making PUT request to cache server: "+str(error))

        # check if request succeeded
        if not req.ok:
            raise InternalServerError("Error putting file in cache server: "+getErrorMessageFromServerResponse(req.text))

        newFilenames = ast.literal_eval(req.content)

        return newFilenames

    def push(self, filename, encryption):
        # make request to cache server
        try:
            req = requests.put("http://"+self.cacheServerAddress+"/push/"+encryption+"/"+filename)
        except requests.exceptions.RequestException as error:
            raise InternalServerError("Error making PUSH request to cache server: "+str(error))

        # check if request succeeded
        if not req.ok:
            if req.status_code == 404:
                raise FileNotFound("PUSH Error, no such file in cache server: "+str(filename))
            else:
                raise InternalServerError("Error during PUSH to cache server")

        return 0

    def info(self, filename, encryption):
        # make request to cache server
        try:
            req = requests.get("http://"+self.cacheServerAddress+"/info/"+encryption+"/"+filename)
        except requests.exceptions.RequestException as error:
            raise InternalServerError("Error making INFO request to cache server: "+str(error))

        # check if request succeeded
        if not req.ok:
            if req.status_code == 404:
                raise FileNotFound("INFO Error, no such file in cache server: "+str(filename))
            else:
                raise InternalServerError("Error getting file info: "+getErrorMessageFromServerResponse(req.text))

        # return file info as dict
        try:
            jsonFileInfo = json.loads(req.text)
        except:
            raise InternalServerError("Error decoding json response")

        return jsonFileInfo
