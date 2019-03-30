#!/usr/bin/env python

import os, sys
import errno
import stat
import fcntl
from hashfs.hashfs_core import HashFS as HashFS_Core

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
        self.local_cache_dir = '/tmp/mkfs'
        self.fs = HashFS_Core()
        # probably want to update this with each change to point to the
        # current FS root

    def getattr(self, path):
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
        out = fuse.Stat()
        out.st_uid = os.getuid()
        out.st_gid = os.getgid()
        out.st_ino = 0
        out.st_dev = 0
        out.st_atime = 0
        out.st_mtime = 0
        out.st_ctime = 0

        if path == '/':
            out.st_mode = stat.S_IFDIR | 0o600
            out.st_nlink = 2
            # Fill st_nlink
            dir_info = self.fs.fetch_dir_info_from_cache(self.root)
            for child, child_info in dir_info.items():
                if child_info['type'] == 'directory':
                    out.st_nlink += 1

            out.st_size = os.path.getsize("{}/{}".format(self.local_cache_dir, self.root))

            return out

        # Get path to the parent directory of the target file/directory
        parent_path = '/'.join(path.strip('/').split('/')[:-1])
        parent_path = '/'+parent_path
        _, parent_node = self.fs.get_node_by_path(self.root, parent_path)
        _, node = self.fs.get_node_by_path(self.root, path)
            
        if parent_node is None or node is None:
            return -errno.ENOENT

        parent_dir_info = self.fs.fetch_dir_info_from_cache(parent_node.node_cksum)
        node_metadata = parent_dir_info[path.split('/')[-1]]

        if node_metadata['type'] == 'file':
            out.st_mode = stat.S_IFREG | 0o700
            out.st_nlink = 1
        elif node_metadata['type'] == 'directory':
            out.st_mode = stat.S_IFDIR | 0o600
            out.st_nlink = 2
            # Fill st_nlink
            dir_info = self.fs.fetch_dir_info_from_cache(node_metadata['cksum'])
            for child, child_info in dir_info.items():
                if child_info['type'] == 'directory':
                    out.st_nlink += 1

        out.st_size = os.path.getsize("{}/{}".format(self.local_cache_dir, node_metadata['cksum']))

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
        #TODO remove an *empty* directory
        # should return -errno.ENOTEMPTY if there's anything in the directory
        nodes_traversed, node = self.fs.get_node_by_path(self.root, path)

        if node == None:
            print("The path doesn't exist")
            return -errno.ENOENT

        if node.node_type != "directory":
            print("{} is not a directory".format(path))
            return -errno.ENOTDIR

        dir_info = self.fs.fetch_dir_info_from_cache(node.node_cksum)
        if dir_info is None:
            print("{} is not an empty directory".format(path))
            return -errno.ENOTEMPTY

        dir_name = path.split('/')[-1]
        self.root = self.fs.delete_node_bubble_up(dir_name, node.node_cksum, nodes_traversed)

    def rename(self, src, dst):
        raise NotImplementedError
        #TODO move a file
        # should return -errno.ENOENT if src doesn't exist
        # there are some edge cases when moving a directory, but it's not
        # critical to get those right in a first pass

    # TODO: handle make_directory error
    def mkdir(self, path, mode):
        #TODO make an empty directory
        # should return -errno.EEXIST if there's already something at path
        # should only create the *last* component, i.e. not like mkdir -p
        # if any parent directory is missing, should return -errno.ENOENT
        new_dir = path.split('/')[-1]
        parent_path = '/'.join(path.strip('/').split('/')[:-1])
        parent_path = '/'+parent_path
        nodes_traversed, parent_node = self.fs.get_node_by_path(self.root, parent_path)

        if parent_node is None:
            return -errno.ENOENT

        parent_dirinfo = self.fs.fetch_dir_info_from_cache(parent_node.node_cksum)
        if parent_dirinfo.get(new_dir) is not None:
            return -errno.EEXIST

        nodes_traversed.append((parent_node.node_name, parent_node.node_cksum))

        self.root = self.fs.make_directory(new_dir, nodes_traversed)

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

    def chmod(self, path, mode):
        pass

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
        #raise NotImplementedError
        #TODO any prep work 
        # should return -errno.ENOENT if path doesn't exist, -errno.ENOTDIR
        # if it's not a directory
        _, node = self.fs.get_node_by_path(self.root, path)

        if node == None:
            print("The path doesn't exist")
            return -errno.ENOENT

        if node.node_type != "directory":
            print("{} is not a directory".format(path))
            return -errno.ENOTDIR

    def readdir(self, path, offset):
        #TODO list directory contents
        # should look something like
        #for e in SOMETHING:
        #    yield fuse.Direntry(e)

        # get node from path, if it doesn't exist or is not a directory, opendir would have failed
        _, node = self.fs.get_node_by_path(self.root, path)

        # Open dir_node and list files
        dir_contents = self.fs.fetch_dir_info_from_cache(node.node_cksum)
        all_dirs = ['.','..']
        all_dirs.extend(dir_contents.keys())
        for name in all_dirs:
            yield fuse.Direntry(str(name))


    def open(self, path, flags):
        #TODO get ready to use a file
        # should (sometimes) check for existence of path and return
        # -errno.ENOENT if it's missing.
        # this call has a lot of variations and edge cases, so don't worry too
        # much about getting things perfect on the first pass.

        _, node = self.fs.get_node_by_path(self.root, path)
        if node is None:
            return -errno.ENOENT

    def read(self, path, length, offset):
        _, node = self.fs.get_node_by_path(self.root, path)
        if node is None:
            return -errno.ENOENT

        with open('{}/{}'.format(self.local_cache_dir, node.node_cksum), "r") as f:
            f.seek(offset, 1)
            buf = f.read(length)

        return buf

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
    server.parser.add_option(mountopt="local_cache_dir", metavar="DIR", default='/tmp/mkfs',
                             help="Specify a local cache directory [default: %default]")
    server.parse(values=server, errex=1)
    print(server.local_cache_dir)
    if not os.path.isdir(server.local_cache_dir):
        print("{} is not a directory")
        sys.exit()
    if server.local_cache_dir[-1] == '/':
        server.local_cache_dir = server.local_cache_dir[:-1]

    server.main()


if __name__ == '__main__':
    main()
