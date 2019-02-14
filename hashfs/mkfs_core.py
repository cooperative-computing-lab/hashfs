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
    nodes_traversed.append(root_node)
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    directory_file = "{}/{}".format(cache_dir, root_node)

    if not os.path.exists(directory_file) and not get_file_from_s3(fs, root_node):
        return None, None

    # Open directory_file and traverse
    dir_content = fetch_dir_info(fs, root_node)

    sub_node = dir_content.get(path_list[0])
    if sub_node == None:
        print("Path ends at {}".format(root_node))
        return nodes_traversed, None
    
    # If node is found, make sure it's cached locally and return
    if len(path_list) == 1:
        node_file = "{}/{}".format(cache_dir, sub_node['cksum'])
        # If node_file is not in cache, try get from parent
        if not os.path.exists(node_file):
            if not get_file_from_s3(fs, sub_node['cksum']):
                print("The node doesn't exisit in s3")
                return nodes_traversed, None
        return nodes_traversed, sub_node['cksum']
    
    # Check if sub_node is directory
    if sub_node['type'] == 'directory':
        return get_node_by_path(fs, sub_node['cksum'], path_list[1:], nodes_traversed)
    else:
        print("{} is not a directory".format(path_list[0]))
        return nodes_traversed, None

def put_file_bubble_up(fs, src_path, dest_path, nodes_traversed):
    cache_dir = "{}/mkfs/{}".format(tempfile.gettempdir(), fs)
    # Directories in the path of new file that does not exist in the fs yet
    new_directories = dest_path[len(nodes_traversed)-1 : -1]
    
    # Put file named as the cksum
    file_cksum = calculate_file_cksum(src_path)
    put_file_to_s3(fs, file_cksum, src_path)

    # Begin bubbling up
    curr_name = dest_path[-1]
    curr_cksum = file_cksum
    curr_type = "file"
    prev_cksum = None
    # Bubble up and create the new directories that do not exist yet
    for new_dir in reversed(new_directories):
        data = {
            curr_name: {
                'name': curr_name,
                'cksum': curr_cksum,
                'type': curr_type
            }
        }

        curr_name = new_dir
        curr_cksum = calculate_directory_cksum(data)
        curr_type = "directory"

        cache_node_path = "{}/{}".format(cache_dir, curr_cksum)
        with open(cache_node_path, "w+") as df:
            json.dump(data, df)
        put_file_to_s3(fs, curr_cksum, cache_node_path)

    # Bubble up and modify exisiting directories
    for existing_dir_cksum in reversed(nodes_traversed):
        data = fetch_dir_info(fs, existing_dir_cksum)

        # previous node is an existing directory, needs to search dir_contents
        # for curr_name using prev_cksum
        if prev_cksum != None: 
            for name, metadata in data.iteritems():
                if metadata['cksum'] == prev_cksum:
                    curr_name = name
                    break

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

        
        prev_cksum = existing_dir_cksum
        curr_name = None
        curr_cksum = calculate_directory_cksum(data)
        curr_type = "directory"
        
        cache_node_path = "{}/{}".format(cache_dir, curr_cksum)
        with open(cache_node_path, "w+") as df:
            json.dump(data, df)
        put_file_to_s3(fs, curr_cksum, cache_node_path)

    return curr_cksum
    
def fetch_dir_info(fs, dir_cksum):
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

