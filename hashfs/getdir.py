from __future__ import print_function
import mkfs_core as mkfs
import sys
import json
import tempfile
import os
import shutil


# TODO: fix to accept /
def GETDIR(fs, dest_path, local_path, root_cksum):
    os.mkdir("{}/{}".format(local_path, dest_path))
    dest_path = mkfs.clean_path(dest_path)
    _, node = mkfs.get_node_by_path(fs, root_cksum, dest_path.split('/'), list([('/', root_cksum)]))

    if node == None:
        print("The path {} doesn't exist".format(dest_path))
        return False

    if node.node_type != "directory":
        print("{} is not a directory".format(dest_path))
        return False

    # Open dir_node and get files, then recurse into directories
    dir_node_path = "{}/mkfs/{}/{}".format(tempfile.gettempdir(), fs, node.node_cksum)
    with open(dir_node_path, "r") as df:
        dir_contents = json.load(df)

    # TODO: OPTMIZE THIS
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    for name, content in dir_contents.iteritems():
        if content['type'] == 'file':
            if not mkfs.load_node_to_cache(fs, content['cksum']):
                print("Cannot fetch {}".format(content['cksum']))
                return False
            shutil.copyfile("{}/{}".format(cache_dir, content['cksum']), "{}/{}/{}".format(local_path, dest_path, name))
        if content['type'] == 'directory':
            if not GETDIR(fs, "{}/{}".format(dest_path, name), local_path, root_cksum):
                return False

    return True
            
if __name__ == "__main__":
    print(GETDIR(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]))
