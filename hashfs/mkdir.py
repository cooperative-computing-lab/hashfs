from __future__ import print_function
import mkfs_core as mkfs
import sys

def MKDIR(fs, dir_path, root_cksum):
    dir_path = dir_path.split('/')
    nodes_traversed = list([('/', root_cksum)])

    if len(dir_path) != 1:
        # Get containing directory node for the new directory
        nodes_traversed, name, cksum = mkfs.get_node_by_path(fs, root_cksum, dir_path[:-1], nodes_traversed)
        if cksum is None:
            return "Unsuccessful"
        nodes_traversed.append((name, cksum))

    return mkfs.make_directory(fs, dir_path[-1], nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(MKDIR(sys.argv[1], sys.argv[2], sys.argv[3])))