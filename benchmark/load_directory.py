from __future__ import print_function
import sys
import os
sys.path.insert(0, '../')

import hashfs.mkfs_core as mkfs
from hashfs.put import PUT
from hashfs.mkdir import MKDIR

def load_directory(dir_name):
    curr_head = "a"
    for dirpath, dirs, files in os.walk(dir_name):
        print("making directory {}".format(dirpath))
        cksum = MKDIR("dummy", dirpath, curr_head) 
        if cksum == "Unsuccessful":
            print("mkdir {} failed".format(dirpath))
            return
        else:
            curr_head = cksum

        for f in files:
            filepath = "{}/{}".format(dirpath, f)
            if not os.path.isfile(filepath): continue
            #print("putting file {}".format(filepath))
            cksum = PUT("dummy", filepath, filepath, curr_head)
            if cksum == "Unsuccessful":
                print("put {} failed".format(filepath))
                return
            else:
                curr_head = cksum

    print(curr_head)


if __name__ == "__main__":
    load_directory(sys.argv[1])
