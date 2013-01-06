import sys
import queue

noResult = object()

class Task:
    def __init__(self, function, args=(), kw={}):
        self.function = function
        self.arguments = args
        self.keywords = kw

        self.done = False
        self.succeeded = False
        self.failed = False
        self.returnValue = noResult
        self.result = noResult
        self.exception = None
        self.exceptionType = None
        self.traceback = None
        self.generator = None

    def perform(self):
        if self.done:
            return noResult
        if self.generator is not None:
            self._runGenerator()
        elif hasattr(self.function, '__iter__'):
            self.generator = iter(self.function)
            self._runGenerator()
        elif self._isIterator(self.function):
            self.generator = self.function
            self._runGenerator()
        else:
            try:
                rslt = self.function(*self.arguments, **self.keywords)      
            except:
                return self._generalException()
            else:
                if self._isIterator(rslt):
                    self.generator = rslt
                    self._runGenerator()
                else:
                    self.result = rslt
                    self.returnValue = rslt
                    self.done = True
                    self.succeeded = True       
        #if self.returnValue == None:
        #    self.returnValue = noResult
        return self.returnValue
    
    def _generalException(self):
        self.exceptionType, self.exception, tb = sys.exc_info()
        self.traceback = tb.tb_next
        self.failed = True
        self.done = True
        return noResult

    @ staticmethod
    def _isIterator(obj):
        
        return hasattr(obj, '__next__')

    def _runGenerator(self):
        try:
            self.returnValue = next(self.generator)
        except StopIteration as stop:
            self.exceptionType, self.exception, tb = sys.exc_info()
            self.result = stop.value
            self.returnValue = stop.value
            self.done = True
            self.succeeded = True
        except:
            return self._generalException()

    def __iter__(self):
        return self

    def __next__(self):
        value = self.perform()
        if self.done:
            raise StopIteration(self.result)
        return value

    @property
    def exceptionTraceback(self):
        return self.traceback
    
            
class Tasks:
    Task = Task

    def __init__(self):
        self.tasks = queue.Queue()

    def put(self, function, *args):
        self.tasks.put(self.Task(function, *args))

    @property
    def count(self):
        return self.tasks.qsize()

    def perform(self):
        task = self.tasks.get()
        task.perform()
        if not task.done:
            self.tasks.put(task)
