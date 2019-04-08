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
        return "Unsuccessful"

    # Get the node of directory the file is to be placed in
    cont_dirpath = '/'.join(dest_path.strip('/').split('/')[:-1])
    cont_dirpath = '/'+cont_dirpath
    nodes_traversed, node = fs.get_node_by_path(root_cksum, cont_dirpath)
    if node is None:
        print("Unable to resolve provided destination path: {}".format(dest_path))
        return "Unsuccessful"
    nodes_traversed.append((node.node_name, node.node_cksum))

    file_name = dest_path.split('/')[-1]
    return fs.put_file_bubble_up(src_path, file_name, nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(PUT(sys.argv[1], sys.argv[2], sys.argv[3])))
