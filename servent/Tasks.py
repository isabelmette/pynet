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
        try:
            rslt = self.function(*self.arguments, **self.keywords)
            try:
                yieldvalue = next(rslt)
                if self.generator:
                    yieldvalue = next(self.generator)
                else:
                    self.generator = rslt
                self.result = yieldvalue
            except StopIteration as stop:
                self.exceptionType, self.exception, tb = sys.exc_info()
                self.result = stop.value
                self.done = True
                self.succeeded = True
            except TypeError:
                self.result = rslt
                self.done = True
                self.succeeded = True
                
            try:
                yieldvalue = next(self.function(*self.arguments, **self.keywords))
                if self.generator:
                        yieldvalue = next(self.generator)
                else:
                    self.generator = self.function(*self.arguments, **self.keywords)
                self.result = yieldvalue
                print("went to here")
            except:
                pass
        except:
            self.exceptionType, self.exception, tb = sys.exc_info()
            #self.exception = err
            self.traceback = tb.tb_next
            #traceback.print_exception(self.exceptionType, self.exception, self.traceback)
            self.failed = True
            return noResult
        
        if self.result == None:
            self.result = noResult
        return self.result
