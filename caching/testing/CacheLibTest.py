import sys
sys.path.insert(0, '../')

from CacheLib import CacheLib
from CacheLib import FileNotFound
from CacheLib import InternalServerError

cache = CacheLib("localhost:9999")

filename = "crest.jpg"
enc = "sha256"
d = "cacheLibTestDir"

try:
	cache.get(filename, enc, d)
except FileNotFound as error:
	print "File not found"
except InternalServerError as error:
	print error

try:
	cache.push(filename, enc)
except FileNotFound as error:
	print "File not found"
except InternalServerError as error:
	print error

try:
	cache.info(filename, enc)
except FileNotFound as error:
	print "File not found"
except InternalServerError as error:
	print error

try:
	newF = cache.put(filename, enc)
	print "PUT file "+newF
except InternalServerError as error:
	print error

try:
	print cache.info(newF, enc)
except FileNotFound as error:
	print "File not found"
except InternalServerError as error:
	print error