import os
import subprocess

"""
The kernel creates the child process by making a duplicate of the
parent process. The child inherits copies of the parent’s data, stack, and heap segments, which it may then modify independently of the parent’s copies. (The program text, which is placed in memory marked as read-only, is shared by the two
processes.)
The child process goes on either to execute a different set of functions in the
same code as the parent, or, frequently, to use the execve() system call to load and
execute an entirely new program. An execve() call destroys the existing text, data,
stack, and heap segments, replacing them with new segments based on the code of
the new program
"""

def child_process():
    print("Child process PID:", os.getpid())
    print("Child process PPID:", os.getppid())

    # Execute a different set of functions
    print("Executing different set of functions in child process")

    # Use execve() to load and execute a new program
    os.execve('/bin/ls', ['/bin/ls', '-l'], os.environ)

def parent_process():
    print("Parent process PID:", os.getpid())

    # Create a child process
    child_pid = os.fork()

    if child_pid == 0:
        # This is the child process
        child_process()
    else:
        # This is the parent process
        print("Parent process created child with PID:", child_pid)

if __name__ == '__main__':
    parent_process()
