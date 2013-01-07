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
    
    @property
    def Servent(self):
        class Servent:
            @staticmethod
            def do(_self, func, args = (), kw = {}):
                self.generator = func(*args, **kw)
        return Servent

    def next(self):
        return next(self.generator)

    def setUp(self):
        self.generator = None
        self.poller = SelectPoller.SelectPoller(self.Servant)

class Test_SelectPoller_IO(SelectPollerTest, test.TimeoutTest):

    def setUp(self):
        SelectPollerTest.setUp(self)
        self.s1, self.s2 = test.socketPair()
        self.c1 = Connection(self.s1)
        self.c2 = Connection(self.s2)
        self.poller.poll(self.c1, self.c2)

    def tearDown(self):
        self.s1.close()
        self.s2.close()

    def test_get_notified_for_read(self):
        self.s1.write(b'hallo')
        self.s1.flush()
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
        self.s1.write(b'1')
        self.s1.flush()
        self.s2.write(b'2')
        self.s2.flush()
        self.next()
        self.next()
        self.assertEqual(self.c1.data, b'2')
        self.assertEqual(self.c1.data, b'1')
       
class Test_SelectPoller(SelectPollerTest):

    def test_poller_does_not_poll_if_there_is_nothing_to_poll(self):
        self.assertEqual(self.generator, None)
        
        

if __name__ == '__main__':
    unittest.main(exit = False)
