import threading
import queue

class Tasks(object):

    def __init__(self):
        self.queue = queue.Queue()

class Servant(object):

    def __init__(self):
        self.lock = threading.RLock()
        self.threads = set()
        self.tasks = Tasks()

    def do(self, *args):
        with self.lock:
            if self.isIdle():
                self.startWatching()
        self.tasks.addNew(*args)

    def isIdle(self):
        with self.lock:
            return not self.threads
