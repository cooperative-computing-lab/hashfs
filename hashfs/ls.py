from __future__ import print_function
import mkfs_core as mkfs
import sys
import json
import tempfile

def LS(fs, dest_path, root_cksum):
    if dest_path == '/':
        node = mkfs.Node('/', root_cksum, "directory")
        if load_node_to_cache(fs, node.node_cksum) == False:
            print("Invalid root: {}".format(root_cksum))
            return
        
    _, node = mkfs.get_node_by_path(fs, root_cksum, dest_path.split('/'), list([('/', root_cksum)]))

    if node == None:
        print("The path doesn't exist")
        return

    # Check if node is a directory
    if node.node_type != "directory":
        print("{} is not a directory".format(dest_path))
        return

    # Open dir_node and list files
    dir_node_path = "{}/mkfs/{}/{}".format(tempfile.gettempdir(), fs, node.node_cksum)
    with open(dir_node_path, "r") as df:
        dir_contents = json.load(df) 
    
    for name, content in dir_contents.iteritems():
        print("{:<12} {:<20}".format(content['type'], name))

if __name__ == "__main__":
    LS(sys.argv[1], sys.argv[2], sys.argv[3])
