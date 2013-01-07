## required imports
import unittest
import unittest.mock as mock
import sys
import threading

## modules to test
import Servant

## test helper
from pynet.test import timeout, TimeoutTest


class Test_Servant_do(unittest.TestCase, TimeoutTest):

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
                yield from range(20)
                l.append(1)
            yield b()
            while l != [1]:
                yield
            s.add(1)
        self.servant.do(a())
        self.assertTimeoutEqual(s, set((1,)))

    def test_parallel_do(self):
        start = []
        s1 = set()
        s2 = set()
        def a():
            s1.add(1)
            timeout(lambda: start, [])
            assert start != []
            s2.add(1)
        def b():
            s1.add(2)
            timeout(lambda: start, [])
            assert start != []
            s2.add(2)
        self.servant.do(a)
        self.servant.do(b)
        self.assertTimeoutEqual(s1, set((1,2)))
        self.assertEqual(s2, set())
        start.append(1)
        self.assertTimeoutEqual(s2, set((1,2)))


        
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

    def test_maximum_thread_count(self):
        mtc = 10
        self.servant.maximumThreadCount = mtc
        self.assertEqual(self.servant.maximumThreadCount, mtc)
        l = threading.Lock()
        l.acquire()
        for i in range(mtc * 2):
            self.servant.do(l.acquire, ())
        self.assertEqual(len(self.servant.threads), mtc)
        i = 0
        for i in range(mtc * 2):
            if l.locked():
                l.release()
                i += 1
            time.sleep(0.001)

    def test_servant_as_decorator(self):
        l = set()
        def g():pass
        _g = g
        @self.servant
        def g(a):
            l.add(a)
            yield
            return 4 + a
        a = g(1)
        b = g(2)
        self.assertEqual(g.__name__, _g.__name__)
        self.assertEqual(g.__qualname__, g.__qualname__)
        self.assertTimeoutEqual(l, set([1,2]))
        timeout(lambda: a.done, False)
        self.assertTrue(a.done)
        self.assertEqual(a.result, 5)
        timeout(lambda: b.done, False)
        self.assertTrue(a.done)
        self.assertEqual(a.result, 5)

    def test_servent_decorator_twice_is_not_allowed(self):
        s = Servant.Servant()
        try:
            @s
            @self.servant
            def g():
                pass
        except ReferenceError as e:
            self.assertEqual(e.args[0], 'Can not start function in two different servants:')
            self.assertEqual(e.args[1], self.servant)
            self.assertEqual(e.args[2], s)

    def test_can_decorate_twice_with_same_servant(self):
        try:
            @self.servant
            @self.servant
            def g():
                pass
        except ReferenceError:
            self.fail()

    def test_decorate_method_in_class(self):
        a = b = None
        class X:
            def a(self):
                nonlocal a
                a = self
            @self.servant
            def b(self):
                nonlocal b
                b = self
        x = X()
        x.a()
        self.assertEqual(a, x)
        y = X()
        _b = b
        y.b()
        timeout(lambda: b, _b)
        self.assertEqual(b, y)

        x = X()
        X.a(x)
        self.assertEqual(a, x)
        y = X()
        _b = b
        X.b(y)
        timeout(lambda: b, _b)
        self.assertEqual(b, y)

##del Test_Servent_do, Test_Servent

class MockThread:
    t = []
    def __init__(self, watcher):
        self.t.append(self)
        self.watcher = watcher
        self.started = False
        self.stopped = False
    
    def start(self):
        self.started = True

    def run(self):
        self.watcher.perform()

    def stop(self):
        self.stopped = True

class MockWatcher(Servant.Watcher):

    Thread = MockThread

class Test_Watcher(unittest.TestCase, TimeoutTest):

    def setUp(self):
        self.watcher = MockWatcher()
        MockThread.t = self.threads = []

    def test_watcher_can_perform(self):
        l = []
        self.watcher.put(l.append, (1,))
        self.assertEqual(l, [])
        self.watcher.perform()
        self.assertEqual(l, [1])

    def test_watcher_starts_and_ends_threads(self):
        l = []
        self.watcher.put(l.append, (1,))
        self.assertEqual(self.threads, [])
        self.watcher.start()
        timeout(lambda: self.threads, [])
        self.assertEqual(len(self.threads), 1)
        thread = self.threads[0]
        self.assertEqual(self.thread.watcher, self.watcher)
        self.assertTimeoutEqual(self.thread.started, True)
        thread.run()
        self.assertTimeoutEqual(self.thread.stopped, True)
        
    def test_watcher_registers_threads_and_removes_them(self):
        t = self.watcher.Thread(self.watcher)
        self.assertEqual(len(self.watcher.threads))
        l = []
        def run():
            timeout(l, [])
        t.run = run
        t.start()


##del Test_Watcher

class Test_Servant_Module(unittest.TestCase, TimeoutTest):

    def test_do(self):
        l = []
        Servant.do(l.append, (3,))
        self.assertTimeoutEqual(l, [3])

    def test_def_function_for_servant(self):
        l = []
        @Servant.servant
        def g():
            l.append(1)
            yield
            timeout(lambda: 2 in l, False)
            assert 2 in l
            yield
            l.append(3)
        g()
        timeout(lambda: 1 in l, False)
        l.append(2)
        timeout(lambda: 3 in l, False)
        self.assertIn(3, l)
    
if __name__ == '__main__':
    unittest.main(exit = False)
