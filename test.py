import time
import socket

TIMEOUT = 0.5
_l = object()

def timeout(functionToBoolean, value_reference = _l, timeout = TIMEOUT):
    if value_reference is _l:
        value_reference = functionToBoolean()
    t = time.time() + timeout
    while t > time.time():
        value = functionToBoolean()
        if value != value_reference:
            break
        time.sleep(0.001)

        
class TimeoutTest:

    timeout = property(timeout)
    
    def assertTimeoutEqual(self, value, expected, *args):
        timeout(lambda: value == expected, False)
        self.assertEqual(value, expected, *args)

if hasattr(socket, 'socketpair'):
    socketPair = socket.socketpair
else:
    def socketPair():
        s = socket.socket()
        s.bind(('localhost', 0))
        s.listen(1)
        s1 = socket.socket()
        s1.connect(('localhost', s.getsockname()[1]))
        s2, addr = s.accept()
        assert addr[1] == s1.getsockname()[1]
