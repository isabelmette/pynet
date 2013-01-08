import traceback
import select
import threading
import pynet.servant.Servant as Servant

class SelectPoller:
    def __init__(self, servant):
        self.servant = servant
        self.descriptors = set()

    def poll(self, *args):
        anInt = 1
        for d in args:
            value = d.fileno()
            if value.__class__ != anInt.__class__ :
                raise ValueError("fileno of object must be int and not"
                                   " {0}".format(value))
            if not(hasattr(d, 'notifyRead') or
                   hasattr(d, 'notifyWrite') or
                   hasattr(d, 'notifyExceptional')):
                   raise AttributeError("{0} must have at least one of the attributes"
                                   " 'notifyRead' 'notifyWrite' "
                                   "'notifyExceptional'".format(d))
            self.descriptors.add(d)
        self.servant.do(self.generator)

    def generator(self):
        while 1:
            i = 0
            if len(self.descriptors) > 0:
                i += 1
                yield i
            else:
                raise StopIteration

    def remove(self, descriptor):
        self.descriptors.remove(descriptor)

##class SelectPoller:
##
##    def __init__(self):
##        self._read = []
##        self._write = []
##        self._exceptional = []
##
##    def _poll(self):
##        while not self._stopped:
##            try:
##                rlist, wlist, xlist = select.select( \
##                    self._read, self._write, self_exceptional)
##                for readFrom in rlist:
##                    yield readfrom.notifyRead()
##                for readFrom in rlist:
##                    yield readfrom.notifyWrite()
##                for readFrom in rlist:
##                    yield readfrom.notifyExceptional()
##            except:
##                traceback.print_exc()
##            yield
##
##    def start(self):
##        if self._read or self._write or self._exceptional:
##            self._thread.start()
##
##    def stop(self):
##        self._stopped = True
##            
##    def addRead(self, fd):
##        assert hasattr(fd, 'fileno'), 'must have fileno for select.select'
##        assert hasattr(fd, 'notifyRead'), 'must be informed if there is data'
##        self._read.append(fd)
##        self.start()
##
##    def removeRead(self, fd):
##        self._read.remove(fd)
##
##    def addWrite(self, fd):
##        assert hasattr(fd, 'fileno'), 'must have fileno for select.select'
##        assert hasattr(fd, 'notifyWrite'), 'must be informed if there is data'
##        self._write.append(fd)
##        self.start()
##
##    def removeWrite(self, fd):
##        self._write.remove(fd)
##
##    def addExceptional(self, fd):
##        assert hasattr(fd, 'fileno'), 'must have fileno for select.select'
##        assert hasattr(fd, 'notifyExceptional'), 'must be informed if there is data'
##        self._exceptional.append(fd)
##        self.start()
##
##    def removeExceptional(self, fd):
##        self._exceptional.remove(fd)
##
##selectPoller = SelectPoller()
##
