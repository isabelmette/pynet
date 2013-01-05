import sys
import traceback

noResult = object()

class Task:
    def __init__(self, function, args=(), kw={}):
        self.function = function
        self.arguments = args
        self.keywords = kw

        self.done = False
        self.succeeded = False
        self.failed = False
        self.result = None
        self.exception = None
        self.exceptionType = None
        self.traceback = None
        self.generator = None

    def perform(self):
        if self.done:
            return noResult
        if self.generator is not None:
            self._runGenerator()
        elif self._isIterable(self.function):
            self.generator = self.function
            self._runGenerator()
        else:
            try:
                rslt = self.function(*self.arguments, **self.keywords)      
            except:
                return self._generalException()
            else:
                if self._isIterable(rslt):
                    self.generator = rslt
                    self._runGenerator()
                else:
                    self.result = rslt
                    self.done = True
                    self.succeeded = True       
        if self.result == None:
            self.result = noResult
        return self.result
    
    def _generalException(self):
        self.exceptionType, self.exception, tb = sys.exc_info()
        #self.exception = err
        self.traceback = tb.tb_next
        #traceback.print_exception(self.exceptionType, self.exception, self.traceback)
        self.failed = True
        return noResult

    @ staticmethod
    def _isIterable(obj):
        return hasattr(obj, '__next__')

    def _runGenerator(self):
        try:
            yieldvalue = next(self.generator)
        except StopIteration as stop:
            self.exceptionType, self.exception, tb = sys.exc_info()
            self.result = stop.value
            self.done = True
            self.succeeded = True
        except:
            return self._generalException()
        else:
            self.result = yieldvalue
            
class Tasks:
    Task = Task
