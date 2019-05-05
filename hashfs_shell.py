#!/usr/bin/env python

from __future__ import print_function
from hashfs.hashfs_core import HashFS
from hashfs.hashfs_cmd import GET, PUT, LS, MKDIR, DELETE

from optparse import OptionParser

def usage():
    print("Commands:")
    print("    GET      [src_path] [dest_path]")
    print("    PUT      [src_path] [dest_path]")
    print("    LS       [path]")
    print("    MKDIR    [path]")
    print("    DELETE   [path]")

def prompt_loop(options):
    root_cksum = options.root
    new_cksums = list([options.root])
    parent = "{}:{}".format(options.host, options.port)
    fs = HashFS(parent_node=parent, local_cache_dir=options.local_cache, local_run=options.local_run, hash_alg=options.hash_alg)

    command = raw_input("> ")
    while command != "exit":
        command = command.split(" ")
        op = command[0]
        args = command[1:]

        if op == "GET":
            if len(args) != 2:
                usage()
            else:
                GET(args[0], args[1], root_cksum, fs)

        elif op == "PUT":
            if len(args) != 2:
                usage()
            else:
                temp = PUT(args[0], args[1], root_cksum, fs)
                if temp != "Unsuccessful":
                    root_cksum = temp
                    new_cksums.append(root_cksum)

        elif op == "LS":
            if len(args) != 1:
                usage()
            else:
                LS(args[0], root_cksum, fs)

        elif op == "MKDIR":
            if len(args) != 1:
                usage()
            else:
                temp = MKDIR(args[0], root_cksum, fs)
                if temp != "Unsuccessful":
                    root_cksum = temp
                    new_cksums.append(root_cksum)

        elif op == "DELETE":
            if len(args) != 1:
                usage()
            else:
                temp = DELETE(args[0], root_cksum, fs)
                if temp != "Unsuccessful":
                    root_cksum = temp
                    new_cksums.append(root_cksum)
        elif op == "usage":
            usage()
        else:
            print("Invalid argument")
            usage()

        print("Current head: {}".format(root_cksum))
        command = raw_input("> ")

    print("Newest head: {}".format(root_cksum))


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-r", "--root", dest="root",
                    default="44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
                    help="Specify a root hash [default: %default]")
    parser.add_option("-k", "--host", dest="host", default="localhost",
                    help="Specify the address of the parent node [default: %default]")
    parser.add_option("-p", "--port", dest="port", default="9999", 
                    help="Specify the port to connect to [default: %default]")
    parser.add_option("-a", "--alg", dest="hash_alg", default="sha256", 
                    help="Specify the hashing algorithm [default: %default]")
    parser.add_option("-c", "--local-cache", dest="local_cache", default="/tmp/mkfs", 
                    help="Specify a local cache directory path [default: %default]")
    parser.add_option("-l", action="store_true", dest="local_run", default=False, 
                    help="Run file system locally, do not put nodes to parent [default: %default]")


    (options, args) = parser.parse_args()
    prompt_loop(options)
