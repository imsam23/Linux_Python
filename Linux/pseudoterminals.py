import os
import pty
import sys

# Create a pseudoterminal pair (master and slave)
master, slave = pty.openpty()

# Launch a shell in the slave terminal
shell = "/bin/bash"
pid = os.fork()

if pid == 0:  # Child process (shell)
    os.dup2(slave, sys.stdin.fileno())
    os.dup2(slave, sys.stdout.fileno())
    os.dup2(slave, sys.stderr.fileno())
    os.execv(shell, [shell])

# Parent process (controlling process)
while True:
    try:
        user_input = input("Enter a command (q to quit): ")
        if user_input.lower() == "q":
            break
        os.write(master, (user_input + "\n").encode())
        output = os.read(master, 4096).decode()
        print(output)
    except EOFError:
        break

os.close(master)
os.close(slave)
