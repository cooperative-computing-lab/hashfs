from __future__ import print_function
from hashfs_core import HashFS
import sys

def DELETE(dest_path, root_cksum, fs = HashFS()):
    nodes_traversed, node = fs.get_node_by_path(root_cksum, dest_path)

    if node.node_cksum is None:
        print("Cannot delete {}".format(dest_path))
        return "Unsuccessful"

    return fs.delete_node_bubble_up(node.node_name, node.node_cksum, nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(DELETE(sys.argv[1], sys.argv[2])))
