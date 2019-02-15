from __future__ import print_function
import mkfs_core as mkfs
import sys

def DELETE(fs, dest_path, root_cksum):
    nodes_traversed = list()
    nodes_traversed, cksum = mkfs.get_node_by_path(fs, root_cksum, dest_path.split('/'), nodes_traversed)

    print(mkfs.delete_file_bubble_up(fs, cksum, nodes_traversed))

DELETE(sys.argv[1], sys.argv[2], sys.argv[3])
