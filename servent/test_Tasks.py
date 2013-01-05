## required imports
import unittest
import unittest.mock as mock
import sys

## modules to test
import Tasks

class Test_Task(unittest.TestCase):

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
        self.assertEqual(t.result, Tasks.noResult)

    def test_no_result_if_no_return(self):
        def f():
            yield 4
        t = self.t(f)
        t.perform()
        self.assertEqual(t.result, None)
        t.perform()
        self.assertTrue(t.done)
        self.assertEqual(t.result, Tasks.noResult)

    def test_new_task_has_no_result(self):
        self.assertEquals(self.t(lambda: 1).result, Tasks.noResult)

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
            
    def test_does_not_call_twice(self):
        l = []
        t = self.t(l.append, (1,))
        t.perform()
        t.perform()
        self.assertEqual(l, [1])
        

def f():
    yield 1
    yield 3
def g():
    yield 2
    yield 4

class Test_Tasks(unittest.TestCase):

    def setUp(self):
        self.tasks = Tasks.Tasks()

    def test_use(self):
        self.tasks.put(f)
        self.tasks.put(g)
        i = 1
        for t in self.tasks.perform:
            self.assertEqual(t, i)
            i += 1
        self.assertEqual(i, 4)

    def test_count(self):
        self.tasks.put(f)
        self.tasks.put(g)
        self.assertEqual(self.tasks.count, 2)
        self.tasks.perform()
        self.assertEqual(self.tasks.count, 2)
        self.tasks.perform()
        self.assertEqual(self.tasks.count, 2)
        self.tasks.perform()
        self.assertEqual(self.tasks.count, 1)
        self.tasks.perform()
        self.assertEqual(self.tasks.count, 0)

    def test_new_task_is_created_by_put(self):
        l = []
        self.tasks.Task = mock.MagicMock(return_value = \
                                         Tasks.Task(l.append, (4,)))
        self.tasks.put(f, 3, 4)
        self.tasks.Task.assert_called_with(f, 3, 4)
        self.tasks.perform()
        self.assetrEqual(l, [4])
        
        
    

    
if __name__ == '__main__':
    unittest.main(exit = False)
