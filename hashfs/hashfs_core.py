from __future__ import print_function
import os
import sys
import json
import hashlib
import shutil

sys.path.insert(0, os.getcwd())
from caching.CacheLib import CacheLib

class HashFS:
    def __init__(self, fs = "dummy", parent_node = "localhost:9999", local_cache_dir = "/tmp/mkfs", local_run = False, hash_alg = "sha256"):
        self.fs = fs
        self.parent = CacheLib(parent_node)
        self.local_cache_dir = local_cache_dir
        self.local_run = local_run
        self.hash_alg = hash_alg

        self.EMPTY_CKSUM = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    class Node:
        def __init__(self, node_name, node_cksum, node_type):
            self.node_name = node_name
            self.node_cksum = node_cksum
            self.node_type = node_type

    # Get file from bucket and save file in local_cache_dir
    # Returns True if successful, False if unsuccessful
    def get_file_from_parent(self, object_name):
        """Get file from parent and save file in local_cache_dir

        Args:
            object_name (str): name of the object

        Returns:
            bool: True for success, False for otherwise
        """

        # Check if local_cache_dir exists
        if not os.path.isdir(self.local_cache_dir):
            try:
                os.makedirs(self.local_cache_dir)
            except os.error:
                print("Cannot create {}".format(self.local_cache_dir))
                return False

        print(object_name, self.local_cache_dir)
        if self.parent.get(object_name, "sha256", self.local_cache_dir) != 0:
            print("Failed to get file from parent")
            return False

        return True

    # Put the file in the bucket
    # Take a list of tuples in the form of (cksum, path)
    # TODO: May want to add "if file exist" check
    def put_file_to_parent(self, file_tups):
        if not self.local_run:
            file_cksums = list()
            filepaths = list()
            for file_tup in file_tups:
                file_cksums.append(file_tup[0])
                filepaths.append(file_tup[1])
            cksums = self.parent.put(filepaths, self.hash_alg)

            # Check to make sure all cksums match
            if len(set(file_cksums)-set(cksums)) != 0:
                raise Exception('PUT MESSED UP')


    def get_node_by_path(self, root_node, path, nodes_traversed = None):
        """Traverse merkle tree and fetch the node by path

        Starting from the root_node, traverse the merkle tree until the node is found or
        an error has occured

        Args:
            root_node       (str) : the cksum of the root_node to traversed from
            path            (str) : the pathname
            nodes_traversed (list): the list to keep track of nodes traversed

        Returns:
            list: the list of nodes traversed including root
            Node: Node structure containing the information on the node. None if an error
                  has occured
        """
        if path == '/':
            if self.load_node_to_cache(root_node) == False:
                print("The node {} doesn't exist in parent".format(root_node))
            return list(), self.Node('/', root_node, 'directory')

        if nodes_traversed is None:
            nodes_traversed = [('/', root_node)]

        if path[0] == '/': 
            path = path[1:]

        path_list = path.split('/')

        # Open directory file
        dir_content = self.fetch_dir_info_from_cache(root_node)

        sub_node = dir_content.get(path_list[0])
        if sub_node == None: # path's immediate directory/file doesn't exist
            #full_path = '/'.join([x[0] for x in nodes_traversed])
            #print("The path {} doesn't exist".format(full_path))
            return nodes_traversed, None
        
        # If node is found, make sure it's cached locally and return
        if len(path_list) == 1:
            if self.load_node_to_cache(sub_node['cksum']) == False:
                print("The node {} doesn't exist in parent".format(sub_node['cksum']))
                return nodes_traversed, None
            return nodes_traversed, self.Node(sub_node['name'], sub_node['cksum'], sub_node['type'])
        
        # Check if sub_node is directory
        if sub_node['type'] == 'directory':
            nodes_traversed.append((path_list[0], sub_node['cksum']))
            return self.get_node_by_path(sub_node['cksum'], '/'.join(path_list[1:]), nodes_traversed)
        else:
            fullpath = "/".join([x[0] for x in nodes_traversed])
            print("{} is not a directory".format(fullpath))
            return nodes_traversed, None


    def put_file_bubble_up(self, src_path, file_name, nodes_traversed):
        """Put file into the file system and bubble up the merkle tree

        Args:
            src_path        (str) : source of file to be placed in the file system
            file_name       (list): name of the file at destination
            nodes_traversed (list): the list to keep track of nodes traversed

        Return:
            str : returns the new root cksum
        """
        # Check that the new file doesn't collide with existing files/directories
        # in the containing directory
        dir_data = self.fetch_dir_info_from_cache(nodes_traversed[-1][1])
        if dir_data.get(file_name) != None and dir_data[file_name]['type'] != 'file':
            print("Attempting to overwrite directory {} as a file".format(file_name))
            return "Failed"

        # Put file named as the cksum
        file_cksum = self.calculate_file_cksum(src_path)
        shutil.copyfile(src_path, "{}/{}".format(self.local_cache_dir, file_cksum))
        self.put_file_to_parent([(file_cksum, src_path)])

        # Bubble up on existing directories
        curr_cksum = self.bubble_up_existing_dir(nodes_traversed, file_name, file_cksum, "file")

        return curr_cksum


    def bubble_up_existing_dir(self, nodes_traversed, curr_name, curr_cksum, curr_type):
        new_nodes = list()
        # Bubble up and modify exisiting directories
        for dir_name, existing_dir_cksum in reversed(nodes_traversed):
            data = self.fetch_dir_info_from_cache(existing_dir_cksum)

            # Check to see if curr_node already exist in the directory
            if data.get(curr_name) == None:
                data[curr_name] = {
                    'name': curr_name,
                    'cksum': curr_cksum,
                    'type': curr_type
                }
            else:
                data[curr_name]['cksum'] = curr_cksum
                data[curr_name]['type'] = curr_type

            
            curr_name = dir_name
            curr_cksum = self.calculate_directory_cksum(data)
            curr_type = "directory"
            
            cache_node_path = self.put_dir_info_in_cache(curr_cksum, data)
            new_nodes.append((curr_cksum, cache_node_path))

        self.put_file_to_parent(new_nodes)

        return curr_cksum

    def delete_node_bubble_up(self, delete_name, delete_cksum, nodes_traversed):
        # Fetch directory containing the node to be removed
        containing_dir = nodes_traversed[-1]
        dir_data = self.fetch_dir_info_from_cache(containing_dir[1])

        if dir_data.pop(delete_name, None) is None:
            print("The node {} is not in the dictionary {}".format(delete_cksum, nodes_traversed[-1][1]))

        new_cksum = self.calculate_directory_cksum(dir_data)
        cache_node_path = self.put_dir_info_in_cache(new_cksum, dir_data)
        self.put_file_to_parent([(new_cksum, cache_node_path)])

        root_cksum = self.bubble_up_existing_dir(nodes_traversed[:-1], containing_dir[0], new_cksum, "directory")

        return root_cksum

    def make_directory(self, dir_name, nodes_traversed):
        data = {}
        dir_cksum = self.calculate_directory_cksum(data)
        cache_node_path = self.put_dir_info_in_cache(dir_cksum, data)
        self.put_file_to_parent([(dir_cksum, cache_node_path)])

        root_cksum = self.bubble_up_existing_dir(nodes_traversed, dir_name, dir_cksum, "directory")

        return root_cksum


    def load_node_to_cache(self, cksum):
        if not os.path.isdir(self.local_cache_dir):
            os.makedirs(self.local_cache_dir)

        if not os.path.exists("{}/{}".format(self.local_cache_dir, cksum)) and not self.get_file_from_parent(cksum):
            return False

        return True

    def put_dir_info_in_cache(self, cksum, data):
        if not os.path.isdir(self.local_cache_dir):
            os.makedirs(self.local_cache_dir)

        cache_node_path = "{}/{}".format(self.local_cache_dir, cksum)
        with open(cache_node_path, "w+") as df:
            json.dump(data, df)

        return cache_node_path
        
    def fetch_dir_info_from_cache(self, dir_cksum):
        if self.load_node_to_cache(dir_cksum) == False:
            return None

        with open("{}/{}".format(self.local_cache_dir, dir_cksum), "r") as df:
            data = json.load(df)

        return data
            
    def calculate_directory_cksum(self, dir_content):
        if self.hash_alg == "sha256":
            hasher = hashlib.sha256()
        elif self.hash_alg == "sha1":
            hasher = hashlib.sha1()
        elif self.hash_alg == "md5":
            hasher = hashlib.md5()

        hasher.update(json.dumps(dir_content))
        
        return hasher.hexdigest()

    def calculate_file_cksum(self, src_filepath):
        if self.hash_alg == "sha256":
            hasher = hashlib.sha256()
        elif self.hash_alg == "sha1":
            hasher = hashlib.sha1()
        elif self.hash_alg == "md5":
            hasher = hashlib.md5()

        with open(src_filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    # Since every path needs to be absolute path from root, remove leading /
    def clean_path(self, path):
        if path[0] == '/':
            return path[1:]
        
        return path
