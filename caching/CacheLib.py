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
        """
        
        Make request to cache server to get file from cache

        Args:
            filename    (str): name of file to be retrieved
            encryption  (str): name of encryption algorithm used in the file name
            dirToSave   (str): name of directory in which to save the file retrieved from cache server

        Returns:
            int: 0 if success

        Raises:
            InternalServerError: if there is an error
            FileNotFound: if the file is not found in the cache server

        """
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
        """
        
        Make request to cache server to put files in the cache

        Args:
            filepaths   (list): list of file names to be put in the cache
            encryption  (str): name of encryption algorithm to be used in the file names

        Returns:
            list: list of filenames that were successfully put in the cache

        Raises:
            InternalServerError: if there is an error

        """
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
        """
        
        Make request to cache server to push a file up

        Args:
            filename    (str): name of file to be pushed up
            encryption  (str): name of encryption algorithm used in the file name

        Returns:
            int: 0 if success

        Raises:
            InternalServerError: if there is an error
            FileNotFound: if the file is not found in the cache server

        """
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
        """
        
        Make request to cache server to get information about a file

        Args:
            filename    (str): name of file to get information about
            encryption  (str): name of encryption algorithm used in the file name

        Returns:
            json: file information in json form

        Raises:
            InternalServerError: if there is an error
            FileNotFound: if the file is not found in the cache server

        """
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
