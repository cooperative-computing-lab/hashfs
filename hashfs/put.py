from __future__ import print_function
import mkfs_core2 as mkfs
import os
import sys

# TODO: think about file and directory with the same name
def PUT(fs, src_path, dest_path, root_cksum):
    # Check if src_path is a local file that exists
    if not os.path.isfile(src_path):
        print("{} is not a valid local path".format(src_path))
        return

    dest_path = dest_path.split('/')
    nodes_traversed = list()
    nodes_traversed, dir_cksum = mkfs.get_node_by_path(fs, root_cksum,
                                                    dest_path, nodes_traversed)

    # Invalid root node
    if nodes_traversed == None:
        print("The root node provided is invalid: {}".format(root_cksum))
        return

    print(mkfs.put_file_bubble_up(fs, src_path, dest_path, nodes_traversed))

PUT(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
