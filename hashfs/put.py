from __future__ import print_function
from hashfs_core import HashFS
import os
import sys

# TODO: think about file and directory with the same name
def PUT(src_path, dest_path, root_cksum):
    fs = HashFS()
    # Check if src_path is a local file that exists
    if not os.path.isfile(src_path):
        print("{} is not a valid local path".format(src_path))
        return

    dest_path = fs.clean_path(dest_path)
    dest_path = dest_path.split('/')
    nodes_traversed = list([('/', root_cksum)])
    # Get the node of directory the file is to be placed in
    if len(dest_path) != 1:
        nodes_traversed, node = fs.get_node_by_path(root_cksum, dest_path[:-1], nodes_traversed)

        # Add containing directory to nodes_traversed
        nodes_traversed.append((node.node_name, node.node_cksum))

        if node.node_cksum == None:
            print("Unable to resolve provided destination path")
            return "Unsuccessful"

    return fs.put_file_bubble_up(src_path, dest_path, nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(PUT(sys.argv[1], sys.argv[2], sys.argv[3])))
