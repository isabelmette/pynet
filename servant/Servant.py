import threading
import Tasks
import time



class Servant(object):
    def __init__(self):
        self.threads = set()
        self.tasks = Tasks.Tasks()
        self.watcherThread = None
        
        
    def isIdle(self):
        return not self.threads

    def do(self, task, *args):
        if self.watcherThread == None:
            self.watcherThread = Watcher(self)
            self.threads.add(self.watcherThread)
            self.watcherThread.start()
        self.tasks.put(task, *args)

    def work():
        while self.tasks.perform():
            pass

class Watcher(threading.Thread):
    def __init__(self, servant):
        threading.Thread.__init__(self)
        self.servant = servant
        self.goal = 0.01
        self.threads = self.servant.threads
        self.queueTimes = []
        self.servant.tasks.subscribe(self)
        self.maxThreads = 799
        self.averageQueueTime = 10000
        
    def run(self):
        while 1:
            if self.servant.tasks.count > 0 and \
               self.averageQueueTime >= self.goal and\
               len(self.threads) < self.maxThreads:
                thread = Worker(self.servant, self)
                self.threads.add(thread)
                thread.start()
            time.sleep(0.001)
                

    
    def stopped(self, thread):
            self.threads.remove(thread)

    def newTask(self, task):
        task.enterTime = time.time()


    def leftQueue(self, task):
        curTime = time.time()
        difference = curTime - task.enterTime
        self.queueTimes.append(difference)
        self.computeAverage()
    

    def computeAverage(self):
        allTimes = sum(self.queueTimes)
        divisor = len(self.queueTimes)
        if divisor > 0:
            self.averageQueueTime = allTimes/float(divisor)
        self.averageQueueTime = 10000

class Worker(threading.Thread):
    
    def __init__(self, servant, watcher):
        threading.Thread.__init__(self)
        self.servant = servant
        self.watcher = watcher

    def run(self):
        try:
            while self.servant.tasks.perform():
                pass
        finally:
            self.watcher.stopped(self)
            
servant = Servant()

def do(task, *args):
    servant.do(task, *args)
