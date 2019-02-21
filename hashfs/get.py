from __future__ import print_function
import mkfs_core as mkfs
import os
import sys
import shutil
import tempfile

def GET(fs, src_path, dest_path, root_cksum):
    _, file_name, file_cksum = mkfs.get_node_by_path(fs, root_cksum, src_path.split('/'), list([('/', root_cksum)]))

    if file_cksum == None:
        print("Failed to retrieve {} from {}".format(src_path, fs))
        return False

    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    shutil.copyfile("{}/{}".format(cache_dir, file_cksum), dest_path)

    return True

if __name__ == "__main__":
    if GET(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]):
        print("Success")
    else:
        print("Failure")
