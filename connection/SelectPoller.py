import traceback
import select
import threading


class SelectPoller():

    import pynet.servant.Servant as servant
    
    def __init__(self):
        self._read = []
        self._write = []
        self._exceptional = []
        self._thread = self.servant.Thread(target = self._poll)
        self._stopped = False

    def _poll(self):
        while not self._stopped:
            try:
                rlist, wlist, xlist = select.select( \
                    self._read, self._write, self_exceptional)
                for readFrom in rlist:
                    yield readfrom.notifyRead()
                for readFrom in rlist:
                    yield readfrom.notifyWrite()
                for readFrom in rlist:
                    yield readfrom.notifyExceptional()
            except:
                traceback.print_exc()
            yield

    def start(self):
        if self._read or self._write or self._exceptional:
            self._thread.start()

    def stop(self):
        self._stopped = True
            
    def addRead(self, fd):
        assert hasattr(fd, 'fileno'), 'must have fileno for select.select'
        assert hasattr(fd, 'notifyRead'), 'must be informed if there is data'
        self._read.append(fd)
        self.start()

    def removeRead(self, fd):
        self._read.remove(fd)

    def addWrite(self, fd):
        assert hasattr(fd, 'fileno'), 'must have fileno for select.select'
        assert hasattr(fd, 'notifyWrite'), 'must be informed if there is data'
        self._write.append(fd)
        self.start()

    def removeWrite(self, fd):
        self._write.remove(fd)

    def addExceptional(self, fd):
        assert hasattr(fd, 'fileno'), 'must have fileno for select.select'
        assert hasattr(fd, 'notifyExceptional'), 'must be informed if there is data'
        self._exceptional.append(fd)
        self.start()

    def removeExceptional(self, fd):
        self._exceptional.remove(fd)

selectPoller = SelectPoller()

