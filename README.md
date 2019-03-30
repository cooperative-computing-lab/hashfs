## HashFS

### Running a Cache Server:
1) Install dependecies
```
curl --location --output virtualenv-16.4.0.tar.gz https://github.com/pypa/virtualenv/tarball/16.4.0
tar xvfz virtualenv-16.4.0.tar.gz
python pypa-virtualenv-bc1d76d/virtualenv.py flask_virtualenv
source flask_virtualenv/bin/activate
pip install flask
pip install requests

```
2) Run server
```
cd hashfs/caching
python CacheServer.py --port 9999 --parent-address 0 --dir /tmp/cache

```

### To run the demo:
After activating the virtualenv and install flask and requests, run the demo script
```
./demo.sh
```
- The script will start up two CacheServer, one will serving as the root while 
  the other will be the caching layer between the root and the filesystem shell.
- The servers will be set to run in the background with all output redirected to
  their respective log files
- It will then prompt for a checksum, please enter 'a'
- Then type usage when prompted at > to see all commands available
- CacheServers will be killed upon exiting the shell.

### FUSE Module
HashFS can be mounted as a file system via FUSE.
The implementation uses the Python package `fuse-python`,
which is available through `pip install`.
Due to dependencies on the host machine's `libfuse` installation,
Python might have trouble with library search.
On RHEL7 machines, for example,
`import fuse` fails searching for `libfuse.so.2`.
The easiest fix is to set `RPATH` when installing.

    pip install --global-option=build_ext --global-option='--rpath=/usr/lib64' fuse-python

To run the FUSE module,

    ./hashfs_fuse -o root=<HASH> -o local_cache_dir=<DIR> <MOUNTPOINT>
