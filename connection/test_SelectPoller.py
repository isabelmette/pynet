import unittest
import SelectPoller
import pynet.test as test
import socket


##@SelectPoller.Read
##@SelectPoller.Write
##class SocketConnection(object):
##    def __init__(self, socket):
##        self.socket = socket
##        self.fileno = socket.fileno
##
##    def notifyRead(self):
##        self.notifiedRead = True
##
##

class Connection:
    def __init__(self, socket):
        self.socket = socket
        self.fileno = socket.fileno
        self.read = 0
        self.write = 0
        self.exceptional = 0
        self.data = None

    def notifyRead(self):
        self.read += 1
        self.data = self.socket.read()
        return 'tritratrullala - read'

    def notifyRead(self):
        self.write += 1
        return 'tritratrullala - write'

    def notifyExceptional(self):
        self.exceptional += 1
        return 'tritratrullala - exceptional'

class SelectPollerTest(unittest.TestCase):

    SelectPoller = SelectPoller.SelectPoller
    
    @property
    def Servant(self):
        class Servant:
            def do(_self, func, args = (), kw = {}):
                self.generator = func(*args, **kw)
        return Servant

    def next(self):
        return next(self.generator)

    def setUp(self):
        self.generator = 'not set'
        self.poller = self.SelectPoller(self.Servant())

    def createConnectionPair(self):
        self.s1, self.s2 = test.socketPair()
        self.c1 = Connection(self.s1)
        self.c2 = Connection(self.s2)


class Test_SelectPoller_IO(SelectPollerTest, test.TimeoutTest):

    def setUp(self):
        SelectPollerTest.setUp(self)
        self.createConnectionPair()
        self.poller.poll(self.c1, self.c2)

    def tearDown(self):
        self.s1.close()
        self.s2.close()

    def test_get_notified_for_read(self):
        self.s1.sendall(b'hallo')
        self.assertTimeoutEqual(self.next, 'tritratrullala - read')
        self.assertEqual(self.c1.data, b'hallo')
        self.assertEqual(self.c1.read, 1)
        
    def test_get_notified_for_write(self):
        self.assertEqual(self.next(), 'tritratrullala - write')
        
    def test_no_notification_for_write_if_closed(self):
        self.s1.close()
        self.assertNotEqual(self.next(), 'tritratrullala - write')

    def test_notification_for_exceptional(self):
        self.s1.close()
        self.assertNotEqual(self.next(), 'tritratrullala - exceptional')

    def test_write_to_both_sockets(self):
        self.s1.sendall(b'1')
        self.s2.sendall(b'2')
        self.next()
        self.next()
        self.assertEqual(self.c1.data, b'2')
        self.assertEqual(self.c1.data, b'1')


class FileNoMock:
    def __init__(self, fileno, r = False, w =  False, e = False):
        self._f = fileno
        self.read = 0
        self.write = 0
        self.exceptional = 0
        self.notified = 0
        if r:
            def notifyRead(self):
                self.read += 1
                self.notified += 1
            self.notifyRead = notifyRead
        if w:
            def notifyWrite(self):
                self.write += 1
                self.notified += 1
            self.notifyWrite = notifyWrite
        if e:
            def notifyExceptional(self):
                self.exceptional += 1
                self.notified += 1
            self.notifyExceptional = notifyExceptional
            
    def fileno(self):
        return self._f

class Test_SelectPoller(SelectPollerTest):

    def test_poller_does_not_poll_if_there_is_nothing_to_poll(self):
        self.assertEqual(self.generator, 'not set')
        
    def test_stops_polling_if_nothing_to_poll(self):
        self.createConnectionPair()
        self.poller.poll(self.c2)
        self.s1.sendall(b'hallo')
        self.next()
        self.poller.remove(self.c2)
        self.assertRaises(StopIteration, self.next)

    def test_poll_no_fileno(self):
        self.assertRaisesRegex(AttributeError,
                               "'.*' object has no attribute 'fileno'", 
                               lambda: self.poller.poll(object()))
        
    def test_poll_bad_fileno(self):
        o = object()
        self.assertRaisesRegex(ValueError,
                               "fileno of object must be int and not"
                               " {0}".format(o), 
                               lambda: self.poller.poll(FileNoMock(o)))

    def test_poll_no_notifyMethods(self):
        m = FileNoMock(1)
        self.assertRaisesRegex(AttributeError,
                               "{0} must have at least one of the attributes"
                               " 'notifyRead' 'notifyWrite' "
                               "'notifyExceptional'".format(m), 
                               lambda: self.poller.poll(m))

class Test_SelectPoller_notify(SelectPollerTest):

    def SelectPoller(self, *args):
        class _SelectPoller(SelectPoller.SelectPoller):
            def select(_self, ):
                return self.select(*args, **kw)
        return _SelectPoller(*args)

    def select(self, r, w, e, timeout = None):
        self.selected = (r[:], w[:], e[:])
        return (r * self.selectSomething,
                w * self.selectSomething,
                e * self.selectSomething)

    def setUp(self):
        SelectPollerTest.setUp(self)
        self.rmock = FileNoMock(1, True)
        self.wmock = FileNoMock(1, False, True)
        self.emock = FileNoMock(1, False, False, True)
        self.selectSomething = 1

    def test_select_read(self):
        mock = self.rmock
        self.poller.poll(mock)
        self.next()
        self.assertEqual(self.selected, ([mock],[],[]))
        self.assertEqual(mock.read, 1)
        
    def test_select_write(self):
        mock = self.wmock
        self.poller.poll(mock)
        self.next()
        self.assertEqual(self.selected, ([],[mock],[]))
        self.assertEqual(mock.write, 1)
    
    def test_select_exceptional(self):
        mock = self.emock
        self.poller.poll(mock)
        self.next()
        self.assertEqual(self.selected, ([],[],[mock]))
        self.assertEqual(mock.exceptional, 1)

    def assert_notified(self, mock, times):
        self.selectSomething = times
        self.poller.poll(mock)
        for i in range(times - 1):
            self.poller.poll(mock)
        self.next()
        self.assertEqual(mock.notified, times * times)
        
    def test_not_notified_if_not_selected_read(self):
        self.assert_notified(self.rmock, 0)
        
    def test_not_notified_if_not_selected_write(self):
        self.assert_notified(self.wmock, 0)

    def test_not_notified_if_not_selected_exceptional(self):
        self.assert_notified(self.emock, 0)

    def test_notified_often_read(self):
        self.assert_notified(self.rmock, 5)

    def test_notified_often_write(self):
        self.assert_notified(self.wmock, 5)
        
    def test_notified_often_exceptional(self):
        self.assert_notified(self.emock, 5)

    def test_notify_many(self):
        rlist = [FileNoMock(1, r = True) for i in range(10)]
        wlist = [FileNoMock(1, w = True) for i in range(30)]
        elist = [FileNoMock(1, e = True) for i in range(20)]
        s = len(rlist) + len(wlist) + len(elist)
        self.poller.poll(*(rlist + wlist + elist))
        for i in range(s):
            self.next()
        for r in rlist:
            self.assertEqual(r.read, 1)
        for w in wlist:
            self.assertEqual(r.write, 1)
        for e in elist:
            self.assertEqual(r.exceptional, 1)

    def test_notify_one_often(self):
        mock = FileNoMock(1, r = True, w = True, e = True)
        self.poller.poll(mock)
        self.select = lambda r, w, e, timeout = None: (r, [], [])
        self.next()
        self.assertEqual(mock.read, 1)
        self.assertEqual(mock.write, 0)
        self.assertEqual(mock.exceptional, 0)
        self.next()
        self.assertEqual(mock.read, 2)
        self.assertEqual(mock.write, 0)
        self.assertEqual(mock.exceptional, 0)
        self.select = lambda r, w, e, timeout = None: ([], w, [])
        self.next()
        self.assertEqual(mock.read, 2)
        self.assertEqual(mock.write, 1)
        self.assertEqual(mock.exceptional, 0)
        self.select = lambda r, w, e, timeout = None: ([], w, e)
        self.next()
        self.next()
        self.assertEqual(mock.read, 2)
        self.assertEqual(mock.write, 2)
        self.assertEqual(mock.exceptional, 1)

if __name__ == '__main__':
    unittest.main(exit = False)
