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
```
./demo.sh
```
- The script will start up two CacheServer, one will serving as the root while 
  the other will be the caching layer between the root and the filesystem shell.
- The servers will be set to run in the background with all output redirected to
  their respective log files
- It will then prompt for a checksum, please enter 'a'
- Then type usage when prompted at > to see all commands available
- p.s. since the servers are running in the background, either exit the terminal
  or kill the processes manually

(LS at / doesn't work yet, needs fixing)
