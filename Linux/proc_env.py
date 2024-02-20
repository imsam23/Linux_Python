import subprocess
import os

# To pass the environment to a child process,
# we can use the environ keyword argument to the subprocess.Popen() function.
child_process = subprocess.Popen(["python", "child_script.py"], env=os.environ.copy())

for name, value in os.environ.items():
    print("{}: {}".format(name, value))

# To replace the environment of a process, we can use the os.execve() function.
# The first argument to os.execve() is the path to the new program that the process should run.
# the following code replaces the current environment with a new environment that contains only the PATH and USER variables:
os.execve("/bin/bash", [], ["PATH=/usr/bin:/bin", "USER=bard"])

for name, value in os.environ.items():
    print("{}: {}".format(name, value))
