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
                raise err.with_traceback(tb)
        t = self.t(f)
        self.assertEqual(t.perform(), Tasks.noResult)
        self.assertFalse(t.succeeded)
        self.assertTrue(t.failed)
        self.assertTrue(t.done)
        self.assertEqual(t.exception, err)
        self.assertEqual(t.exceptionType, ty)
        self.assertEqual(t.traceback.tb_next, tb)
        self.assertEqual(t.exceptionTraceback.tb_next, tb)

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

    def test_result_of_yield_from(self):
        def g():
            def f():
                yield 4
                return 9
            x = yield from f()
            return x + 5
        t = self.t(g)
        self.assertEqual(t.perform(), 4)
        self.assertEqual(t.perform(), 9)
        self.assertEqual(t.perform(), 14)
        self.assertEqual(t.perform(), Tasks.noResult)
        self.assertEqual(t.result, 14)

    def test_result_of_a_function(self):
        o = object()
        def f():
            return o
        t = self.t(f)
        t.perform()
        self.assertEqual(t.result, o)

    def test_result_on_error(self):
        def f():
            raise
        t = self.t(f)
        t.perform()
        self.assertEqual(t.result, None)

    def test_no_result_if_no_return(self):
        def f():
            yield 4
        t = self.t(f)
        t.perform()
        self.assertEqual(t.result, None)
        t.perform()
        self.assertTrue(t.done)
        self.assertEqual(t.result, None)

    def test_works_with_any_iterable(self):
        t = self.t(range(1,4))
        self.assertEqual(t.perform(), 1)
        self.assertEqual(t.perform(), 2)
        self.assertEqual(t.perform(), 3)
        self.assertEqual(t.perform(), Tasks.noResult)

    def test_iteration_over_task(self):
        t = self.t(range(2))
        l = iter(t)
        self.assertEqual(next(l), 0)
        self.assertEqual(next(l), 1)
        for i in l:
            self.fail('iterator did not stop')
            
        

    

    
if __name__ == '__main__':
    unittest.main(exit = False)
