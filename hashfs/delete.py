from __future__ import print_function
import mkfs_core as mkfs
import sys

def DELETE(fs, dest_path, root_cksum):
    nodes_traversed = list([('/', root_cksum)])
    nodes_traversed, name, cksum = mkfs.get_node_by_path(fs, root_cksum, dest_path.split('/'), nodes_traversed)

    if cksum is None:
        print("Cannot delete {}".format(dest_path))
        return "Unsuccessful"

    return mkfs.delete_node_bubble_up(fs, name, cksum, nodes_traversed)

if __name__ == "__main__":
    print("New head: {}".format(DELETE(sys.argv[1], sys.argv[2], sys.argv[3])))
