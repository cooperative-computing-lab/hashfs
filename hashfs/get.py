from __future__ import print_function
from hashfs_core import HashFS
import os
import sys
import shutil
import tempfile

def GET(src_path, dest_path, root_cksum):
    fs = HashFS()
    src_path = fs.clean_path(src_path)
    _, node = fs.get_node_by_path(root_cksum, src_path.split('/'), list([('/', root_cksum)]))

    if node == None:
        return False

    cache_dir = "{}/mkfs".format(tempfile.gettempdir())
    shutil.copyfile("{}/{}".format(cache_dir, node.node_cksum), dest_path)

    return True

if __name__ == "__main__":
    if GET(sys.argv[1], sys.argv[2], sys.argv[3]):
        print("Success")
    else:
        print("Failure")
