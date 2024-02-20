import os
import select

def watch_file(filename):
    kq = select.kqueue()
    file_descriptor = os.open(filename, os.O_RDONLY)

    kevent = select.kevent(file_descriptor, filter=select.KQ_FILTER_VNODE, flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE, fflags=select.KQ_NOTE_WRITE)

    kq.control([kevent], 0, 0) # registers the event with the Kqueue

    try:
        while True:
            events = kq.control([], 1, None)
            for event in events:
                print(f"File {filename} has been modified")
    except KeyboardInterrupt:
        pass
    finally:
        kq.close()
        os.close(file_descriptor)

if __name__ == "__main__":
    watch_file("test.txt")
