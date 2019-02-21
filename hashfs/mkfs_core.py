from __future__ import print_function
import os
import boto3
import json
import hashlib
import tempfile
import botocore

s3 = boto3.resource('s3',
                    endpoint_url='http://localhost:9000',
                    aws_access_key_id='7FJTEI4TFG2QQTS03PN0',
                    aws_secret_access_key='VwLxI1A0YIX0ZcS3nPV44PdolnxTaT5eYWLU+QZV',
                    config=botocore.client.Config(signature_version='s3v4'),
                    region_name='us-east-1')


# Get file from bucket and save file in /tmp/mkfs/<fs>/
# Returns True if successful, False if unsuccessful
def get_file_from_s3(fs, object_name):
    """Get file from parent and save file in /tmp/mkfs/<fs>/

    Args:
        fs          (str): name of the file system instance
        object_name (str): name of the object

    Returns:
        bool: True for success, False for otherwise
    """

    # Check if /tmp/mkfs/<fs>/ exists
    local_cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    if not os.path.isdir(local_cache_dir):
        try:
            os.makedirs(local_cache_dir)
        except os.error:
            print("Cannot create {}".format(local_cache_dir))
            return False

    try:
        s3.Bucket(fs).download_file(object_name, "{}/{}".format(local_cache_dir, object_name))
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise

    return True

# Put the file in the bucket
# TODO: May want to add "if file exist" check
def put_file_to_s3(fs, object_name, local_name):
    s3.Bucket(fs).upload_file(local_name, object_name)

# root_node: cksum of root directories to begin search from
# TODO: Check if node is directory when traversing
def get_node_by_path(fs, root_node, path_list, nodes_traversed):
    """Traverse merkle tree and fetch the node by path

    Starting from the root_node, traverse the merkle tree until the node is found or
    an error has occured

    Args:
        fs              (str) : name of the file system instance
        root_node       (str) : the cksum of the root_node to traversed from
        path_list       (list): the pathname list
        nodes_traversed (list): the list to keep track of nodes traversed

    Returns:
        list: the list of nodes traversed including root
        str : the name of the node found (None if an error occured)
        str : the cksum of the node found (None if an error occured)
    """
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    directory_file = "{}/{}".format(cache_dir, root_node)

    # Load node to cache before proceeding
    if load_node_to_cache(fs, root_node) == False:
        print("Unable to load node {} from parent".format(root_node))
        return None, None, None

    # Open directory_file and traverse
    dir_content = fetch_dir_info_from_cache(fs, root_node)

    sub_node = dir_content.get(path_list[0])
    if sub_node == None:
        fullpath = "/".join([x[0] for x in nodes_traversed])
        print("Path ends at {}".format(fullpath))
        return nodes_traversed, None, None
    
    # If node is found, make sure it's cached locally and return
    if len(path_list) == 1:
        if load_node_to_cache(fs, sub_node['cksum']) == False:
            print("The node {} doesn't exist in s3".format(sub_node['cksum']))
            return nodes_traversed, None, None
        return nodes_traversed, sub_node['name'], sub_node['cksum']
    
    # Check if sub_node is directory
    if sub_node['type'] == 'directory':
        nodes_traversed.append((path_list[0], sub_node['cksum']))
        return get_node_by_path(fs, sub_node['cksum'], path_list[1:], nodes_traversed)
    else:
        fullpath = "/{}".format("/".join([x[0] for x in nodes_traversed]))
        print("{} is not a directory".format(fullpath))
        return nodes_traversed, None

def put_file_bubble_up(fs, src_path, dest_path, nodes_traversed):
    """Put file into the file system and bubble up the merkle tree

    Args:
        fs              (str) : name of the file system instance
        src_path        (str) : source of file to be placed in the file system
        dest_path       (list): the path list to place the file at
        nodes_traversed (list): the list to keep track of nodes traversed

    Return:
        str : returns the new root cksum
    """
    # Check that the new file doesn't collide with existing files/directories
    # in the containing directory
    dir_data = fetch_dir_info_from_cache(fs, nodes_traversed[-1][1])
    if dir_data.get(dest_path[-1]) != None and dir_data[dest_path[-1]]['type'] != 'file':
        print("Attempting to overwrite directory {} as a file".format(dest_path))
        return "Failed"

    # Put file named as the cksum
    file_cksum = calculate_file_cksum(src_path)
    put_file_to_s3(fs, file_cksum, src_path)

    # Bubble up on existing directories
    curr_cksum = bubble_up_existing_dir(fs, nodes_traversed, dest_path[-1], file_cksum, "file")

    return curr_cksum


def bubble_up_existing_dir(fs, nodes_traversed, curr_name, curr_cksum, curr_type):
    # Bubble up and modify exisiting directories
    for dir_name, existing_dir_cksum in reversed(nodes_traversed):
        data = fetch_dir_info_from_cache(fs, existing_dir_cksum)

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
        curr_cksum = calculate_directory_cksum(data)
        curr_type = "directory"
        
        cache_node_path = put_dir_info_in_cache(fs, curr_cksum, data)
        put_file_to_s3(fs, curr_cksum, cache_node_path)

    return curr_cksum

def delete_node_bubble_up(fs, delete_name, delete_cksum, nodes_traversed):
    # Fetch directory containing the node to be removed
    containing_dir = nodes_traversed[-1]
    dir_data = fetch_dir_info_from_cache(fs, containing_dir[1])

    if dir_data.pop(delete_name, None) is None:
        print("The node {} is not in the dictionary {}".format(delete_cksum, nodes_traversed[-1][1]))

    new_cksum = calculate_directory_cksum(dir_data)
    cache_node_path = put_dir_info_in_cache(fs, new_cksum, dir_data)
    put_file_to_s3(fs, new_cksum, cache_node_path)

    root_cksum = bubble_up_existing_dir(fs, nodes_traversed[:-1], containing_dir[0], new_cksum, "directory")

    return root_cksum

def make_directory(fs, dir_name, nodes_traversed):
    data = {}
    dir_cksum = calculate_directory_cksum(data)
    cache_node_path = put_dir_info_in_cache(fs, dir_cksum, data)
    put_file_to_s3(fs, dir_cksum, cache_node_path)

    root_cksum = bubble_up_existing_dir(fs, nodes_traversed, dir_name, dir_cksum, "directory")

    return root_cksum


def load_node_to_cache(fs, cksum):
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    if not os.path.exists("{}/{}".format(cache_dir, cksum)) and not get_file_from_s3(fs, cksum):
        return False

    return True

def put_dir_info_in_cache(fs, cksum, data):
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    cache_node_path = "{}/{}".format(cache_dir, cksum)
    with open(cache_node_path, "w+") as df:
        json.dump(data, df)

    return cache_node_path
    
def fetch_dir_info_from_cache(fs, dir_cksum):
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    with open("{}/{}".format(cache_dir, dir_cksum), "r") as df:
        data = json.load(df)

    return data
        
def calculate_directory_cksum(dir_content):
    hasher = hashlib.sha256()
    hasher.update(json.dumps(dir_content))
    
    return hasher.hexdigest()

def calculate_file_cksum(src_filepath):
    hasher = hashlib.sha256()
    with open(src_filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

