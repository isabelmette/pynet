import time

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
