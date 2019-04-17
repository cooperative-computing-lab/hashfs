import sys
import time
sys.path.insert(0, '../')

from CacheLib import CacheLib
from CacheLib import FileNotFound
from CacheLib import InternalServerError

cache = CacheLib("localhost:9999")

filename = "crest.jpg"
enc = "sha256"
d = "cacheLibTestDir"

N = 50
files = ["crest.jpg" for _ in range(N)]

t1 = time.time()
for _ in range(N):
	cache.put(files, enc)
print time.time() - t1

t2 = time.time()
for _ in range(N*N):
	cache.put("crest.jpg", enc)
print time.time() - t2

# try:
# 	cache.get(filename, enc, d)
# except FileNotFound as error:
# 	print "File not found"
# except InternalServerError as error:
# 	print error

# try:
# 	cache.push(filename, enc)
# except FileNotFound as error:
# 	print "File not found"
# except InternalServerError as error:
# 	print error

# try:
# 	cache.info(filename, enc)
# except FileNotFound as error:
# 	print "File not found"
# except InternalServerError as error:
# 	print error

# try:
# 	newF = cache.put(filename, enc)
# 	print "PUT file "+newF
# except InternalServerError as error:
# 	print error

# try:
# 	print cache.info(newF, enc)
# except FileNotFound as error:
# 	print "File not found"
# except InternalServerError as error:
# 	print error