



class Task:
    def __init__(self, function, args=(), kw={}):
        self.function = function
        self.arguments = args
        self.keywords = kw

        self.done = False
        self.succeeded = False
        self.failed = False

    def perform(self):
        try:
            self.function(*self.arguments, **self.keywords)
        except Exception as err:
            print(err)
            self.failed = True
            return
        self.done = True
        self.succeeded = True
