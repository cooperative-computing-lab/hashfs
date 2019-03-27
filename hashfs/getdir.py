from __future__ import print_function
from hashfs_core import HashFS
import sys
import json
import tempfile
import os
import shutil


# TODO: fix to accept /
def GETDIR(dest_path, local_path, root_cksum):
    os.mkdir("{}/{}".format(local_path, dest_path))
    dest_path = fs.clean_path(dest_path)
    _, node = fs.get_node_by_path(root_cksum, dest_path.split('/'), list([('/', root_cksum)]))

    if node == None:
        print("The path {} doesn't exist".format(dest_path))
        return False

    if node.node_type != "directory":
        print("{} is not a directory".format(dest_path))
        return False

    # Open dir_node and get files, then recurse into directories
    dir_node_path = "{}/mkfs/{}".format(tempfile.gettempdir(), node.node_cksum)
    with open(dir_node_path, "r") as df:
        dir_contents = json.load(df)

    # TODO: OPTMIZE THIS
    cache_dir = "{}/mkfs".format(tempfile.gettempdir())
    for name, content in dir_contents.iteritems():
        if content['type'] == 'file':
            if not fs.load_node_to_cache(content['cksum']):
                print("Cannot fetch {}".format(content['cksum']))
                return False
            shutil.copyfile("{}/{}".format(cache_dir, content['cksum']), "{}/{}/{}".format(local_path, dest_path, name))
        if content['type'] == 'directory':
            if not GETDIR(fs, "{}/{}".format(dest_path, name), local_path, root_cksum):
                return False

    return True
            
if __name__ == "__main__":
    print(GETDIR(sys.argv[1], sys.argv[2], sys.argv[3]))
