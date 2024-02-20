import os
import select

def print_numbers_and_listen():
    kq = select.kqueue()

    # Watch for user input on standard input (file descriptor 0)
    i = 1

    while True:
        print(f"Current number: {i}")
        i += 1

        # timeout of 1 second
        event = [select.kevent(0, filter=select.KQ_FILTER_READ, flags=select.KQ_EV_ADD)]
        events = kq.control(event, 1, 1)

        if events:
            for e in events:
                if e.filter == select.KQ_FILTER_READ:
                    # User input is available, read it
                    user_input = os.read(0, 1024).strip().decode('utf-8')
                    print(f"You entered: {user_input}")

if __name__ == "__main__":
    print_numbers_and_listen()
