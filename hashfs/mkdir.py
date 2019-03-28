from __future__ import print_function
from hashfs_core import HashFS
import sys

def MKDIR(dir_path, root_cksum):
    fs = HashFS()

    # Get the node of directory the file is to be placed in
    cont_dirpath = '/'.join(dir_path.strip('/').split('/')[:-1])
    cont_dirpath = '/'+cont_dirpath
    nodes_traversed, node = fs.get_node_by_path(root_cksum, cont_dirpath)
    if node is None:
        return "Unsuccessful"
    nodes_traversed.append((node.node_name, node.node_cksum))

    return fs.make_directory(dir_path.split('/')[-1], nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(MKDIR(sys.argv[1], sys.argv[2])))
