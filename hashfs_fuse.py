#!/usr/bin/env python

import os, sys
import errno
import stat
import fcntl
from hashfs.mkfs_core import get_node_by_path
from hashfs.mkfs_core import Node

# from examples in libfuse/python-fuse
# pull in some spaghetti to make this stuff work without fuse-py being installed
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
from fuse import Fuse


if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

fuse.feature_assert('stateful_files', 'has_init')

# Not implemented:
# - symlink
# - link
# - truncate
# - mknod
# - ioctl
# - fsinit
# - getxattr
# - setxattr
# - listxattr
# - removexattr
# - lock
# - create (handled by open)
# - fgetattr
# - ftruncate
# - chmod
# - chown
# - fsyncdir
# - releasedir
# - fsync
# - flush


# For all of these functions, you can return -errno.ENOENT if the path doesn't
# exist, or -errno.ENOTDIR if a path component is not a directory

class HashFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)

        #FIXME set up a default root
        self.root = 'a'
        # probably want to update this with each change to point to the
        # current FS root

    def getattr(self, path):
        out = fuse.Stat()
        out.st_uid = os.getuid()
        out.st_gid = os.getgid()

        raise NotImplementedError
        #TODO fill in missing stat fields
        # the most important ones:
        # - st_ino: can probably be 0 for now, but should be chosen better.
        #       An easy solution is grabbing the inode number of the backing
        #       file in the cache, as someone else is managing it. Could also
        #       assign sequentially or randomly.
        # - st_mode: should be stat.S_IFDIR | 0o700 for directories,
        #       stat.S_IFREG | 0o600, other types such as symlinks have
        #       different values
        # - st_size: size in bytes of on-disk contents (file contents, symlink
        #       target, directory listing, etc.)
        # - st_nlink: should be 1 for files, 2 + the number of immediate
        #       subdirectories for directories

        return out

    def readlink(self, path):
        raise NotImplementedError
        #TODO not supporting symlinks at the moment, so this should just
        # return -errno.ENOENT if path doesn't exist, -errno.EINVAL otherwise

    def unlink(self, path):
        raise NotImplementedError
        #TODO delete a file
        # should return -errno.EISDIR if path is a directory

    def rmdir(self, path):
        raise NotImplementedError
        #TODO remove an *empty* directory
        # should return -errno.ENOTEMPTY if there's anything in the directory

    def rename(self, src, dst):
        raise NotImplementedError
        #TODO move a file
        # should return -errno.ENOENT if src doesn't exist
        # there are some edge cases when moving a directory, but it's not
        # critical to get those right in a first pass

    def mkdir(self, path, mode):
        raise NotImplementedError
        #TODO make an empty directory
        # should return -errno.EEXIST if there's already something at path
        # should only create the *last* component, i.e. not like mkdir -p
        # if any parent directory is missing, should return -errno.ENOENT

    def utime(self, path, times):
        # silently ignore
        pass

    def utimens(self, path, ts_acc, ts_mod):
        # silently ignore
        pass

    def access(self, path, mode):
        raise NotImplementedError
        #TODO since we're not enforcing permissions, it's OK to just check
        # for existence and do nothing. If path doesn't exist, should
        # return -errno.ENOENT

    def statfs(self):
        out = fuse.StatVFS()
        # preferred size of file blocks, in bytes
        out.f_bsize = 4096
        # fundamental size of file blcoks, in bytes
        out.f_frsize = 4096


        #TODO fill in file system summary info
        # total number of blocks in the filesystem
        out.f_blocks = 0 
        # number of free blocks
        out.f_bfree = 0
        # total number of file inodes
        out.f_files = 0
        # nunber of free file inodes
        out.f_ffree = 0

        return out

    def opendir(self, path):
        raise NotImplementedError
        #TODO any prep work 
        # should return -errno.ENOENT if path doesn't exist, -errno.ENOTDIR
        # if it's not a directory

    def readdir(self, path, offset):
        #TODO list directory contents
        # should look something like
        #for e in SOMETHING:
        #    yield fuse.Direntry(e)
        dest_path = mkfs.clean_path(dest_path)
        _, node = mkfs.get_node_by_path(fs, root_cksum, dest_path.split('/'), list([('/', root_cksum)]))

        if node == None:
            print("The path doesn't exist")
            return -errno.ENOENT

        # Check if node is a directory
        if node.node_type != "directory":
            print("{} is not a directory".format(dest_path))
            return -errno.ENOENT

        # Open dir_node and list files
	dir_contents = fetch_dir_info_from_cache("hashfs", node.node_cksum)
        for name in '.', '..', dir_contents.keys():
            yield fuse.Direntry(name)

    def open(self, path, flags, *mode):
        #TODO get ready to use a file
        # should (sometimes) check for existence of path and return
        # -errno.ENOENT if it's missing.
        # this call has a lot of variations and edge cases, so don't worry too
        # much about getting things perfect on the first pass.
        node = get_node_by_path("hashfs", self.root, path.split("/"), [])
        if node is None:
            return -errno.ENOENT
        return os.open(node.node_cksum, "r+b") # open for read+write without truncation as binary file

    def read(self, path, length, offset, fh):
        return os.pread(fh, length, offset)

    def write(self, path, buf, offset):
        raise NotImplementedError
        #TODO write buf at offset bytes into the file and return the
        # number of bytes written

    def release(self, path, flags):
        pass
        #TODO commit any buffered changes to the file

    def main(self, *a, **kw):
        return Fuse.main(self, *a, **kw)


def main():
    server = HashFS(version="%prog " + fuse.__version__,
                    usage="A FUSE implementation of HashFS." + Fuse.fusage,
                    dash_s_do='setsingle')

    server.parser.add_option(mountopt="root", metavar="HASH", default='a',
                             help="Specify a root hash [default: %default]")
    server.parse(values=server, errex=1)

    server.main()


if __name__ == '__main__':
    main()
