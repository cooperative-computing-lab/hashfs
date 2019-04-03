import time
import os
import sys

def run_command(cmd):
    real_time = time.time()
    os.system(cmd)
    return time.time() - real_time

# -- main execution --
if len(sys.argv) < 3:
    print "usage: fuse_benchmark.py regular_dir fuse_dir"
    sys.exit()

regular_dir = sys.argv[1]
if regular_dir[-1] == '/':
    regular_dir = regular_dir[:-1]

fuse_dir = sys.argv[2]
if fuse_dir[-1] == '/':
    fuse_dir = fuse_dir[:-1]

list_of_commands = ["cp -r ../cctools-7.0.9-x86_64-redhat7 {}/cctools",
                    "tar -cvzf /tmp/cctools.tar.gz {}/cctools",
                    "ls -lR {}/cctools",
                    "rm -r {}/cctools"]
info = []
totalRegularTime = 0
totalFuseTime = 0
for cmd in list_of_commands:
    reg_time = run_command(cmd.format(regular_dir))
    fuse_time = run_command(cmd.format(fuse_dir))
    totalRegularTime += reg_time
    totalFuseTime += fuse_time
    info.append("Regular "+cmd.split(' ')[0]+" "+cmd.split(' ')[1]+": "+str(reg_time))
    info.append("FUSE "+cmd.split(' ')[0]+" "+cmd.split(' ')[1]+": "+str(fuse_time))

for info_str in info:
    print info_str
print "----------"
print "Regular - total time: "+str(totalRegularTime)
print "FUSE - total time: "+str(totalFuseTime)
