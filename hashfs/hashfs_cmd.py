from __future__ import print_function
from hashfs_core import HashFS
import os
import sys
import json
import shutil
import tempfile

def GET(src_path, dest_path, root_cksum, fs = HashFS()):
    _, node = fs.get_node_by_path(root_cksum, src_path)

    if node == None:
        return False

    shutil.copyfile("{}/{}".format(fs.local_cache_dir, node.node_cksum), dest_path)

    return True

# TODO: think about file and directory with the same name
def PUT(src_path, dest_path, root_cksum, fs = HashFS()):
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

def LS(dest_path, root_cksum, fs = HashFS()):
    _, node = fs.get_node_by_path(root_cksum, dest_path)
    if node == None:
        print("The path does't exist")
        return

    # Check if node is a directory
    if node.node_type != "directory":
        print("{} is not a directory".format(dest_path))
        return

    # Open dir_node and list files
    dir_node_path = "{}/{}".format(fs.local_cache_dir, node.node_cksum)
    with open(dir_node_path, "r") as df:
        dir_contents = json.load(df) 
    
    for name, content in dir_contents.iteritems():
        print("{:<12} {:<20}".format(content['type'], name))

def MKDIR(dir_path, root_cksum, fs = HashFS()):
    # Get the node of directory the file is to be placed in
    cont_dirpath = '/'.join(dir_path.strip('/').split('/')[:-1])
    cont_dirpath = '/'+cont_dirpath
    nodes_traversed, node = fs.get_node_by_path(root_cksum, cont_dirpath)
    if node is None:
        return "Unsuccessful"
    nodes_traversed.append((node.node_name, node.node_cksum))

    return fs.make_directory(dir_path.split('/')[-1], nodes_traversed)

def DELETE(dest_path, root_cksum, fs = HashFS()):
    nodes_traversed, node = fs.get_node_by_path(root_cksum, dest_path)

    if node.node_cksum is None:
        print("Cannot delete {}".format(dest_path))
        return "Unsuccessful"

    return fs.delete_node_bubble_up(node.node_name, node.node_cksum, nodes_traversed)
