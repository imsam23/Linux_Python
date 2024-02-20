"""
https://python.hotexamples.com/examples/select/-/kqueue/python-kqueue-function-examples.html
"""
import os
import select
import time
from select import kqueue


def start_monitor(dirs):
    last_run = time.time()
    files_stats = []
    paths = []
    current_dir = os.getcwd()

    kq = kqueue()

    source_events = []
    for dir_name in dirs:
        dir_path = current_dir + '/' + dir_name
        paths.append(dir_path)
        fd = os.open(dir_path, os.O_RDONLY)
        event = select.kevent(fd, filter=select.KQ_FILTER_VNODE,
                              flags=select.KQ_EV_ADD | select.KQ_EV_CLEAR,
                              fflags=select.KQ_NOTE_WRITE)
        source_events.append(event)

    while True:
        events = kq.control(source_events,  len(source_events), 2000)
        if any(map(lambda e: e.fflags & select.KQ_NOTE_WRITE, events)):
            if (time.time() - last_run) < LIMIT:
                continue
            if check_modifications(current_dir, paths):
                try:
                    async_test(["make", "test"])
                    os.system('clear')
                    subprocess.Popen("neurotic")
                except NeuroticError as ne:
                    os.system('clear')
                    if b"ERROR" in ne.content[0]:
                        print(ne.content[0])
                    else:
                        subprocess.Popen("neurotic")
                last_run = time.time()


def watch_files(filenames):
    def _watch_file(kq, filename, flags = select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_ONESHOT, fflags = select.KQ_NOTE_WRITE | select.KQ_NOTE_DELETE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_RENAME):
        fd = os.open(filename, os.O_RDONLY)
        event = [select.kevent(fd, filter=select.KQ_FILTER_VNODE, flags=flags, fflags=fflags)]
        kq.control(event, 0, 0)
        return fd
    kq = select.kqueue()
    # filedescriptors -> filename
    fds = {}
    for filename in filenames:
        # expand out '~/' nonsense if its their
        filename = os.path.expanduser(filename)
        # get absolute path if its relative
        filename = os.path.abspath(filename)
        fds[_watch_file(kq, filename)] = filename
    try:
        """This block of code waits for events on the kernel event queue. 
        The kq.control call waits indefinitely for an event to occur.
         Once events are received, they are stored in the events variable."""
        events = kq.control([], 1, None)
    finally:
        kq.close()
        for fd in fds:
            os.close(fd)

    changed_files = set()
    for event in events:
        changed_files.add(fds[event.ident])

    return changed_files