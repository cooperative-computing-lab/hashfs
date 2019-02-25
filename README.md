## HashFS

### Running a Cache Server:
1) Install dependecies
```
curl --location --output virtualenv-16.4.0.tar.gz https://github.com/pypa/virtualenv/tarball/16.4.0
tar xvfz virtualenv-16.4.0.tar.gz
python pypa-virtualenv-bc1d76d/virtualenv.py myVE
source myVE/bin/activate
pip install flask
pip install requests

```
2) Run server
```
cd hashfs/caching
python CacheServer.py --port 9999 --parent-address 0 --dir /tmp/cache

```

### Running mkfs_shell
1) Start a CacheServer with port 9999 (mkfs_core.py hardcodes to use this port for now)
2) Inside the directory created for cache data from starting a CacheServer, create a text file named 'a' with '{}' inside as string, this serves as the initial root directory with no content inside
3) Run the mkfs_shell. The shell will prompt for namespace and root checksum, enter random value for namespace (was used as bucket name when dealing with s3) and 'a' for the root checksum for the first run
```
python mkfs_shell.py
```
4) Type usage when prompted at > to see all commands available

(LS at / doesn't work, needs fixing)
