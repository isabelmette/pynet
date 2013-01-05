## required imports
import unittest
import sys

## modules to test
import Tasks

class Test_FunctionTask(unittest.TestCase):

    t = Tasks.Task

    def test_create(self):
        f = lambda: None
        t = self.t(f, (1,2,3,4), {'a':3})
        self.assertEqual(t.function, f)
        self.assertEqual(t.arguments, (1,2,3,4))
        self.assertEqual(t.keywords, {'a':3})

    def test_simple(self):
        l = []
        def f(*args, **kw):
            l.append(args)
            l.append(kw)
        t = self.t(f, (1,2,3), {'x':2})
        self.assertFalse(t.done)
        self.assertEqual(l, [])
        t.perform()
        self.assertTrue(t.done)
        self.assertTrue(t.succeeded)
        self.assertFalse(t.failed)
        self.assertEqual(l, [(1,2,3), {'x':2}])
        
    def test_on_error(self):
        exception = Exception('smile')
        ty = err = tb = None
        def f():
            nonlocal ty, err, tb
            try:
                raise exception
            except Exception:
                ty, err, tb = sys.exc_info()
                err.__traceback__ = tb
                raise err
        t = self.t(f)
        self.assertEqual(t.perform(), Tasks.noResult)
        self.assertFalse(t.succeeded)
        self.assertTrue(t.failed)
        self.assertTrue(t.done)
        self.assertEqual(t.exception, err)
        self.assertEqual(t.exceptionType, ty)
        self.assertEqual(t.traceback, tb)
        self.assertEqual(t.exceptionTraceback, tb)

    def test_perform_twice(self):
        l = []
        t = self.t(lambda: l)
        self.assertIs(t.perform(), l)
        self.assertEqual(t.perform(), Tasks.noResult)

    def test_generator(self):
        def g():
            yield 1
            yield 2
        t = self.t(g)
        self.assertEqual(t.perform(), 1)
        self.assertEqual(t.perform(), 2)
        self.assertFalse(t.done)
        self.assertEqual(t.perform(), Tasks.noResult)
        self.assertTrue(t.succeeded)
        self.assertFalse(t.failed)
        self.assertTrue(t.done)
        self.assertEqual(t.exceptionType, StopIteration)
        self.assertEqual(t.exception.__class__, StopIteration)
        self.assertEqual(t.traceback, None)

    def test_start_task_with_started_generator(self):
        def g():
            yield 3
        t = self.t(g())
        self.assertEqual(t.perform(), 3)
        self.assertEqual(t.perform(), Tasks.noResult)

    
if __name__ == '__main__':
    unittest.main(exit = True)
