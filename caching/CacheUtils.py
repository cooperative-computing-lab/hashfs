import os
import hashlib

# returns true if file exists, false otherwise
def doesFileExist(cacheDir, filename):
    try:
        if filename not in os.listdir(cacheDir):
            return False
    except IOError as error:
        print error
        return False

    return True

# get's the <p> tag text from a server error response
def getErrorMessageFromServerResponse(text):
    preP = text.split("<p>")
    if len(preP) > 1:
        postP = preP[1].split("</p>")
        return postP[0]
    else:
        return text

# if directory doesn't exist, create it, and return dir name
def validateDirectory(dirPath):
    if len(dirPath) == 0:
        return dirPath
    else:
        # validate directory string
        if dirPath[-1] != "/":
            dirPath = dirPath+"/"

        # create directory if it doesn't already exist
        try:
            if not os.path.isdir(dirPath):
                os.makedirs(dirPath)
                # Create default root directory of an empty directory
                hasher = hashlib.sha256()
                hasher.update("{}")
                print("Creating {}/{}".format(dirPath, hasher.hexdigest()))
                with open(dirPath+"/"+hasher.hexdigest(), "w") as f:
                    f.write("{}")
                # Create a node that represent empty files
                hasher2 = hashlib.sha256()
                print("Creating {}/{}".format(dirPath, hasher2.hexdigest()))
                with open(dirPath+'/'+hasher2.hexdigest(), "w") as f:
                    pass
        except OSError as error:
            return -1
    return dirPath

def calculate_file_cksum(src_filepath):
    hasher = hashlib.sha256()
    with open(src_filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def calculate_binary_data_cksum(data):
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()

def getDirSize(dir):
    return sum(os.path.getsize(f) for f in os.listdir(dir) if os.path.isfile(f))