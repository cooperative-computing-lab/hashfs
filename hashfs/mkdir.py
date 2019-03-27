from __future__ import print_function
from hashfs_core import HashFS
import sys

def MKDIR(dir_path, root_cksum):
    fs = HashFS()
    dir_path = fs.clean_path(dir_path)
    dir_path = dir_path.split('/')
    nodes_traversed = list([('/', root_cksum)])

    if len(dir_path) != 1:
        # Get containing directory node for the new directory
        nodes_traversed, node = fs.get_node_by_path(root_cksum, dir_path[:-1], nodes_traversed)
        nodes_traversed.append((node.node_name, node.node_cksum))
        if node.node_cksum is None:
            return "Unsuccessful"

    return fs.make_directory(dir_path[-1], nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(MKDIR(sys.argv[1], sys.argv[2])))
