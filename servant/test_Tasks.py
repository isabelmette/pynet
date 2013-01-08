## required imports
import unittest
import unittest.mock as mock
import sys
import threading
import test

## modules to test
import Tasks

def handle_error(ty, err, tb):
    pass

class Test_Task(unittest.TestCase, test.TimeoutTest):

    t = Tasks.Tasks.Task

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
        error = []
        def f():
            nonlocal ty, err, tb
            try:
                raise exception
            except Exception:
                ty, err, tb = sys.exc_info()
                raise err.with_traceback(tb)
        t = self.t(f, onError = lambda *args: error.append(args))
        self.assertEqual(t.perform(), Tasks.noResult)
        self.assertFalse(t.succeeded)
        self.assertTrue(t.failed)
        self.assertTrue(t.done)
        self.assertEqual(t.exception, err)
        self.assertEqual(t.exceptionType, ty)
        self.assertEqual(t.traceback.tb_next, tb)
        self.assertEqual(t.exceptionTraceback.tb_next, tb)
        self.assertEqual(error[0][0], ty)
        self.assertEqual(error[0][1], err)
        self.assertEqual(error[0][2].tb_next, tb)

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
        self.assertEqual(t.perform(), None)
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
        self.assertEqual(t.perform(), None)

    def test_result_of_yield_from(self):
        def g():
            def f():
                yield 4
                return 9
            x = yield from f()
            return x + 5
        t = self.t(g)
        self.assertEqual(t.perform(), 4)
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

    def test_result_of_a_function_can_be_None(self):
        def f():
            return None
        t = self.t(f)
        t.perform()
        self.assertEqual(t.result, None)

    def test_result_on_error(self):
        def f():
            raise
        t = self.t(f, onError = handle_error)
        t.perform()
        self.assertEqual(t.result, Tasks.noResult)

    def test_no_result_if_no_return(self):
        def f():
            yield 4
        t = self.t(f)
        t.perform()
        self.assertEqual(t.result, Tasks.noResult)
        t.perform()
        self.assertTrue(t.done)
        self.assertEqual(t.result, None)

    def test_new_task_has_no_result(self):
        self.assertEqual(self.t(lambda: 1).result, Tasks.noResult)

    def test_works_with_any_iterable(self):
        t = self.t(range(1,4))
        self.assertEqual(t.perform(), 1)
        self.assertEqual(t.perform(), 2)
        self.assertEqual(t.perform(), 3)
        self.assertEqual(t.perform(), None)
        self.assertEqual(t.perform(), Tasks.noResult)

    def test_iteration_over_task(self):
        t = self.t(range(2))
        l = iter(t)
        self.assertEqual(next(l), 0)
        self.assertEqual(next(l), 1)
        for i in l:
            self.fail('iterator did not stop')

    def test_completed_task_stops_always_with_result(self):
        o = object()
        def g():
            yield 1
            return o
        t = self.t(g)
        next(t)
        for i in range(10):
            try:
                next(t)
            except StopIteration as s:
                self.assertEqual(s.args[0], o)
            
    def test_does_not_call_twice(self):
        l = []
        t = self.t(l.append, (1,))
        t.perform()
        t.perform()
        self.assertEqual(l, [1])

    def test_raised_TypeError_in_function(self):
        def f():
            yield 1
            raise TypeError('smile')
        t = self.t(f, onError = handle_error)
        t.perform()
        self.assertEqual(t.succeeded, False)
        self.assertEqual(t.done, False)
        t.perform()
        self.assertEqual(t.exception.args, ('smile',))
        self.assertEqual(t.exceptionType, TypeError)

    def test_foul_iterator(self):
        class FoulIterator:
            def __iter__(self):
                raise
        for t in (self.t(FoulIterator, onError = handle_error), \
                  self.t(FoulIterator(), onError = handle_error)):
            t.perform()
            self.assertFalse(t.succeeded)
            self.assertTrue(t.done)
            self.assertTrue(t.failed)

    def test_valid_objects_for_Taks(self):
        class X():
            pass
        self.assertTrue(self.t.accept(X))
        x = X()
        self.assertFalse(self.t.accept(x))
        for attr in ('__call__', '__iter__', '__next__'):
            x = X()
            self.assertFalse(hasattr(x, attr), attr) # precondition for test
            setattr(X, attr, lambda: None)
            self.assertTrue(hasattr(x, attr), attr) # precondition for test
            self.assertTrue(self.t.accept(x), attr)
            delattr(X, attr)

    @unittest.skip('not needed yet')
    def test_stop_task(self):
        l = []
        def f():
            try:
                yield 1
            except self.t.StopError:
                l.append(1)
                raise
        t = self.t(f, onError = handle_error)
        t.perform()
        t.stop()
        self.assertEqual(l, [1])
        self.assertEqual(t.exceptionClass, self.t.StopError)

    @unittest.skip('not needed yet')
    def test_stop_task_that_can_not_be_stopped(self):
        t = self.t(range(4))
        t.perform()
        self.assertRaisesRegex(TypeError, 'Can not stop .* without '\
                                'throw\\(\\)', \
                                lambda: t.stop())

    def test_on_error_traceback_is_default_handler(self):
        import traceback
        _tb_pe = traceback.print_exception
        try:
            traceback.print_exception = pe = mock.MagicMock()
            def f():
                raise NameError(1,2,3)
            t = self.t(f)
            t.perform()
        finally:
            traceback.print_exception = _tb_pe
        self.assertEqual(pe.call_args[0][0], NameError)
        self.assertEqual(pe.call_args[0][1].args, (1,2,3))

    def test_iterate_and_error(self):
        def g():
            raise TabError('bad tabby')
        t = self.t(g, onError = handle_error)
        for i in range(5):
            self.assertRaisesRegex(TabError, 'bad tabby',
                                   lambda: next(t))

    def test_task_does_nothing_if_generator_is_running(self):
        l = threading.Lock()
        l.acquire()
        v = []
        @self.t
        def f():
            v.append(0)
            l.acquire()
            yield
            v.append(1)
        threading.Thread(target = f.perform).start()
        self.assertTimeoutEqual(v, [0])
        self.assertEqual(f.perform(), Tasks.noResult)
        self.assertFalse(f.done)
        self.assertFalse(f.succeeded)
        self.assertFalse(f.failed)
        l.release()
        self.assertTimeoutEqual(v, [0,1])

    def test_yield_from_running_generator_is_an_error(self):
        l = threading.Lock()
        l.acquire()
        v = []
        def f():
            l.acquire()
            yield
        p = f()
        def g():
            yield from p # ValueError: generator already executing
        t = self.t(g, onError = handle_error)
        threading.Thread(target = lambda: next(p)).start()
        self.assertEqual(t.perform(), Tasks.noResult)
        self.assertTrue(t.done)
        self.assertTrue(t.failed)
        self.assertEqual(t.exceptionType, ValueError)
        self.assertEqual(t.exception.args[0], 'generator already executing')
        l.release()

def f():
    yield 1
    return 3
def g():
    yield 2
    return 4

class Test_Tasks(unittest.TestCase):

    def setUp(self):
        self.tasks = Tasks.Tasks()

    def test_use(self):
        self.tasks.put(f)
        self.tasks.put(g)
        i = 1
        while self.tasks.perform():
            i += 1
        self.assertEqual(i, 4)

    def test_execute_tasks_until_done(self):
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
        self.assertEqual(l, [4])
        
    def test_tasks_are_executed_in_put_order(self):
        l = []
        r = range(10)
        for i in r:
            self.tasks.put(l.append, (i,))
        while self.tasks.perform(): pass
        self.assertEqual(l, list(r))

    def test_execute_and_parallelize(self):
        l = []
        def f(a, b, x = 1, y = 2):
            l.extend([a, b, x, y])
            def g():
                l.append(1)
                yield
                l.append(2)
                yield
                l.append(3)
            yield g
            yield from range(100)
            l.append(4)
        self.tasks.put(f, (5, 6), {'x':8, 'y':9})
        while self.tasks.perform(): pass
        self.assertEqual(l, [5, 6, 8, 9, 1, 2, 3, 4])

    def test_no_tasks_can_not_perform(self):
        self.assertEqual(self.tasks.perform(), False)

    def test_fork_with_iterator(self):
        def f():

            yield f()
        self.tasks.put(f())
        for i in range(101):
            self.tasks.perform()
        self.assertGreaterEqual(self.tasks.count, 2)
                
if __name__ == '__main__':
    unittest.main(exit = False)
