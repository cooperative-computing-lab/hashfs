## HashFS

### Running a Cache Server:
1) Install dependecies
```
$ curl --location --output virtualenv-16.4.0.tar.gz https://github.com/pypa/virtualenv/tarball/16.4.0
$ tar xvfz virtualenv-16.4.0.tar.gz
$ source pypa-virtualenv-YYYYYY/myVE/bin/activate
$ pip install flask
$ pip install requests
```
2) Run server
```
cd caching
python CacheServer.py --port portNum --parent-address address --dir directory
```
