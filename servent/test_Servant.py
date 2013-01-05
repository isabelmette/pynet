## required imports
import unittest
import threading
import sys

## modules to test
import Servant

## test helper
from test import timeout, TimeoutTest


class Test_Servent_do(unittest.TestCase, TimeoutTest):

    def setUp(self):
        self.servant = Servant.Servant()

    def test_do(self):
        l = []
        self.servant.do(l.append, (3,))
        self.assertTimeoutEqual(l, [3])

    def test_parallel(self):
        s = set()
        def a():
            while not 1 in s:
                yield
            s.add(2)
            while not 3 in s:
                yield
            s.add(4)
        def b():
            s.add(1)
            while not 2 in s:
                yield
            s.add(3)
            while not 4 in s:
                yield
            s.add(5)
        self.servant.do(a)
        self.servant.do(b)
        self.assertTimeoutEqual(s, set((1,2,3,4,5)))
        
    def test_wait_for_result(self):
        s = set()
        def a():
            s.add(1)
            def b():
                s.add(2)
                yield 5
            yield from b()
        self.servant.do(a())
        self.assertTimeoutEqual(s, set((1,2)))

    def test_do_in_parallel(self):
        l = []
        s = set()
        def a():
            def b():
                yield from range(1000)
                l.append(1)
            yield b()
            while l != [1]:
                yield
            s.add(1)
        self.servant.do(a())
        self.assertTimeoutEqual(s, set((1,)))

    def test_parallel_do(self):
        l = []
        s = set()
        def a():
            timeout(lambda: 1 in l, False)
            assert 1 in l
            s.add(1)
        def b():
            timeout(lambda: 2 in l, False)
            assert 2 in l
            s.add(2)
        self.servant.do(a)
        self.servant.do(b)
        self.assertTimeoutEqual(s, set((1,2)))


        
class Test_Servant(unittest.TestCase, TimeoutTest):

    def setUp(self):
        self.servant = Servant.Servant()

    def test_idle_servant_has_no_threads(self):
        self.assertTrue(self.servant.isIdle())
        self.assertEqual(len(self.servant.threads), 0)

    if hasattr(sys, '_current_frames') and callable(sys._current_frames):
        def test_new_servant_does_not_start_threads(self):
            thread_count = len(sys._current_frames())
            l = []
            for i in range(5):
                l.append(Servant.Servant())
            self.assertEqual(len(sys._current_frames()), thread_count)

    def test_servant_with_one_task_starts_worker_and_watcher_thread(self):
        l = []
        s = set()
        def task():
            timeout(lambda: l, [])
            s.add(l[0])
        self.servant.do(task)
        timeout(lambda: len(self.servant.threads) != 2, True)
        self.assertEqual(len(self.servant.threads), 2)
        self.assertFalse(self.servant.isIdle())
        l.append(1)
        self.assertTimeoutEqual(s, set((1,)))
        
    
if __name__ == '__main__':
    unittest.main(exit = False)
