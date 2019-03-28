from __future__ import print_function
from hashfs.get import GET
from hashfs.put import PUT
from hashfs.ls import LS
from hashfs.mkdir import MKDIR
from hashfs.delete import DELETE

def usage():
    print("Commands:")
    print("    GET      [src_path] [dest_path]")
    print("    PUT      [src_path] [dest_path]")
    print("    LS       [path]")
    print("    MKDIR    [path]")
    print("    DELETE   [path]")


if __name__ == "__main__":
    root_cksum = raw_input("Enter root checksum: ")

    new_cksums = list([root_cksum])

    command = raw_input("> ")
    while command != "exit":
        command = command.split(" ")
        op = command[0]
        args = command[1:]

        if op == "GET":
            if len(args) != 2:
                usage()
                continue
            GET(args[0], args[1], root_cksum)

        elif op == "PUT":
            if len(args) != 2:
                usage()
                continue
            temp = PUT(args[0], args[1], root_cksum)
            if temp != "Unsuccessful":
                root_cksum = temp
                new_cksums.append(root_cksum)

        elif op == "LS":
            if len(args) != 1:
                usage()
                continue
            LS(args[0], root_cksum)

        elif op == "MKDIR":
            if len(args) != 1:
                usage()
                continue
            temp = MKDIR(args[0], root_cksum)
            if temp != "Unsuccessful":
                root_cksum = temp
                new_cksums.append(root_cksum)

        elif op == "DELETE":
            if len(args) != 1:
                usage()
                continue
            temp = DELETE(args[0], root_cksum)
            if temp != "Unsuccessful":
                root_cksum = temp
                new_cksums.append(root_cksum)
        elif op == "usage":
            usage()

        print("Current head: {}".format(root_cksum))
        command = raw_input("> ")

    print("Newest head: {}".format(root_cksum))
