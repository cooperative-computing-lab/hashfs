import os

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
        except OSError as error:
            print "Error creating specified directory: "+str(error)
            return -1
    return dirPath