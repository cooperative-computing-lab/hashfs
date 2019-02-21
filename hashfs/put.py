from __future__ import print_function
import mkfs_core as mkfs
import os
import sys

# TODO: think about file and directory with the same name
def PUT(fs, src_path, dest_path, root_cksum):
    # Check if src_path is a local file that exists
    if not os.path.isfile(src_path):
        print("{} is not a valid local path".format(src_path))
        return

    dest_path = dest_path.split('/')
    nodes_traversed = list([('/', root_cksum)])
    # Get the node of directory the file is to be placed in
    nodes_traversed, dir_name, dir_cksum = mkfs.get_node_by_path(fs, root_cksum,
                                                    dest_path[:-1], nodes_traversed)
    # Add containing directory to nodes_traversed
    nodes_traversed.append((dir_name, dir_cksum))

    # Invalid root node
    if nodes_traversed == None:
        print("The root node provided is invalid: {}".format(root_cksum))
        return "Unsuccessful"

    if dir_cksum == None:
        print("Unable to resolve provided destination path")
        
        return "Unsuccessful"

    return mkfs.put_file_bubble_up(fs, src_path, dest_path, nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(PUT(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])))
