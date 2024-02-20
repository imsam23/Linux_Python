import os
import signal

def child_process():
    print("Child process PID:", os.getpid())

    # Simulate the child process being killed by a signal
    os.kill(os.getpid(), signal.SIGTERM)

def parent_process():
    print("Parent process PID:", os.getpid())

    # Create a child process
    child_pid = os.fork()
    t = os.environ

    if child_pid == 0:
        # This is the child process
        child_process()
    else:
        # This is the parent process
        print("Parent process created child with PID:", child_pid)
        # Wait for the child process to terminate
        pid, status = os.wait()
        print(f"Child process with PID {pid} terminated with status {status}")

if __name__ == '__main__':
    parent_process()
