#!/usr/bin/env bash

# Starts the root server
python caching/CacheServer.py --port 9998 --parent-address 0 --dir test_cache_root >> root_log.txt 2>&1 &
# Starts the cache server with root as parent and mkfs_shell will connect to this
python caching/CacheServer.py --port 9999 --parent-address localhost:9998 --dir test_cache >> cache_log.txt 2>&1 &

# Make sure the flask launches and directories created
sleep 2
echo "{}" > "./test_cache_root/a"

# Run mkfs_shell.py
python mkfs_shell.py

# Kill CacheServers
ps -ef | grep 'python caching/CacheServer.py --port 9998' | grep -v grep | awk '{print $2}' | xargs kill
ps -ef | grep 'python caching/CacheServer.py --port 9999' | grep -v grep | awk '{print $2}' | xargs kill
