#!/usr/bin/env python

import os, sys, shutil
import errno
import stat
import fcntl

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

class SimpleFS(Fuse):

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.opened_files = dict()

    def _full_path(self, partial):
        if partial == "/":
            return "newMountedDir/"
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join('newMountedDir/', partial)
        return path

    def getattr(self, path):
        #full_path = self._full_path(path)
        #st = os.lstat(full_path)
        #return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
        #             'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        path = self._full_path(path)
        if not os.path.exists(path):
            return -errno.ENOENT

        out = fuse.Stat()
        out.st_uid = os.getuid()
        out.st_gid = os.getgid()
        out.st_ino = 0
        out.st_dev = 0
        out.st_atime = 0
        out.st_mtime = 0
        out.st_ctime = 0

        if os.path.isdir(path):
            out.st_mode = stat.S_IFDIR | 0o600
            out.st_nlink = 2
            for entry in os.listdir(path):
                if os.path.isdir(entry):
                    out.st_nlink += 1
        else:
            out.st_mode = stat.S_IFREG | 0o700
            out.st_nlink = 1

        out.st_size = os.path.getsize(path)

        return out

    def readlink(self, path):
        raise NotImplementedError
        #TODO not supporting symlinks at the moment, so this should just
        # return -errno.ENOENT if path doesn't exist, -errno.EINVAL otherwise

    def unlink(self, path):
        return os.unlink(self._full_path(path))

    def rmdir(self, path):
        full_path = self._full_path(path)
        return os.rmdir(full_path)

    def rename(self, old, new):
        raise NotImplementedError
        #return os.rename(self._full_path(old), self._full_path(new))

    def mknod(self, path, mode, dev):
        return os.mknod(self._full_path(path), mode, dev)

    # TODO: handle make_directory error
    def mkdir(self, path, mode):
        return os.mkdir(self._full_path(path), mode)

    def utime(self, path, times):
        # silently ignore
        pass

    def utimens(self, path, ts_acc, ts_mod):
        # silently ignore
        pass

    def access(self, path, mode):
        #TODO since we're not enforcing permissions, it's OK to just check
        # for existence and do nothing. If path doesn't exist, should
        # return -errno.ENOENT
        path = self._full_path(path)
        if not os.path.exists(path):
            return -errno.ENOENT

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
        path = self._full_path(path)
        if not os.path.exists(path):
            return -errno.ENOENT
        if not os.path.isdir(path):
            return -errno.ENOTDIR

    def readdir(self, path, offset):
        full_path = self._full_path(path)
        
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield fuse.Direntry(str(r))

    #def create(self, path, mode, fi=None):
    #    full_path = self._full_path(path)
    #    return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    def open(self, path, flags):
        full_path = self._full_path(path)
        if not os.path.exists(full_path):
            return -errno.ENOENT

        if (flags & os.O_WRONLY) or (flags & os.O_RDWR):
            print "we out here\n"
            tmp = "{}/temp{}".format("/tmp/mkfs2", full_path.replace('/', '_'))
            shutil.copyfile(full_path, tmp)
            fh = os.open(tmp, flags)
            self.opened_files[full_path] = (fh, flags, tmp)
        else:
            fh = os.open(full_path, flags)
            self.opened_files[full_path] = (fh, flags, None)

    def read(self, path, length, offset):
        full_path = self._full_path(path)
        fh = self.opened_files[full_path][0]
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset):
        full_path = self._full_path(path)
        fh = self.opened_files[full_path][0]
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def release(self, path, flags):
        full_path = self._full_path(path)
        if full_path in self.opened_files:
            (fh, flags, tmp_name) = self.opened_files[full_path]
            if (flags & os.O_WRONLY ) or (flags & os.O_RDWR):
                shutil.move(tmp_name, full_path)
            os.close(fh)
            del self.opened_files[full_path]

    def main(self, *a, **kw):
        return Fuse.main(self, *a, **kw)


def main():
    server = SimpleFS(version="%prog " + fuse.__version__,
                    usage="A FUSE implementation of HashFS." + Fuse.fusage,
                    dash_s_do='setsingle')
    server.parse()
    server.main()


if __name__ == '__main__':
    main()
