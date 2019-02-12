from __future__ import print_function
import mkfs_core as mkfs
import sys
import json
import tempfile

def LS(fs, dest_path, root_cksum):
    _, dir_cksum = mkfs.get_node_by_path(fs, root_cksum, dest_path.split('/'), list())

    if dir_cksum == None:
        print("The path doesn't exist")
        return

    # Open dir_node and list files
    dir_node_path = "{}/mkfs/{}/{}".format(tempfile.gettempdir(), fs, dir_cksum)
    with open(dir_node_path, "r") as df:
        dir_contents = json.load(df) 
    
    for name, content in dir_contents.iteritems():
        print("{:<12} {:<20}".format(content['type'], name))

LS(sys.argv[1], sys.argv[2], sys.argv[3])
