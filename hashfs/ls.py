from __future__ import print_function
from hashfs_core import HashFS
import sys
import json
import tempfile

def LS(dest_path, root_cksum):
    fs = HashFS()

    if dest_path == '/':
        node = fs.Node('/', root_cksum, "directory")
        if fs.load_node_to_cache(node.node_cksum) == False:
            print("Invalid root: {}".format(root_cksum))
            return
    else:
        dest_path = fs.clean_path(dest_path)
        _, node = fs.get_node_by_path(root_cksum, dest_path.split('/'), list([('/', root_cksum)]))

    if node == None:
        print("The path doesn't exist")
        return

    # Check if node is a directory
    if node.node_type != "directory":
        print("{} is not a directory".format(dest_path))
        return

    # Open dir_node and list files
    dir_node_path = "{}/mkfs/{}".format(tempfile.gettempdir(), node.node_cksum)
    with open(dir_node_path, "r") as df:
        dir_contents = json.load(df) 
    
    for name, content in dir_contents.iteritems():
        print("{:<12} {:<20}".format(content['type'], name))

if __name__ == "__main__":
    LS(sys.argv[1], sys.argv[2])
