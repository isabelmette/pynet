import sys

from LocalObjectDatabase import LocalObjectDatabase

from proxy import ProxyWithExceptions, insideProxy, outsideProxy
from multiprocessing.pool import ApplyResult

class Objectbase(LocalObjectDatabase):
    pass
assert Objectbase() is objectbase

## optimize: use weak db in some cases

class BoundProxyMethod(object):
    def __init__(self, call, reference, methodName):
        self.call = call
        self.reference = reference
        self.methodName = methodName

    def __call__(self, *args, **kw):
        return self.call(self.reference, self.methodName, args, kw)

class Proxy(ProxyWithExceptions):
    exceptions = ('__reduce__', '__reduce_ex__')

    BoundProxyMethod = BoundProxyMethod

    @insideProxy
    def __init__(self, call, reference):
        self.call = call
        self.reference = reference
        self.initArguments = call, reference

    @insideProxy
    def call(self, methodName, args, kw):
        return self.method(self.reference, methodName, args, kw)

    @insideProxy
    def getReference(self):
        return self.reference

    @insideProxy
    def __reduce__(self):
        return self.__class__, self.initArguments

    @classmethod
    def isProxy(cls, obj):
        return issubclass(type(obj), cls)

    @insideProxy
    def __getattribute__(self, name):
        return self.bindMethod(name)

    @insideProxy
    def bindMethod(self, name):
        return self.BoundProxyMethod(self.call, self.reference, name)

#
# proxy methods for asynchronous send only
#

def _send_execute(reference, methodName, args, kw):
    assert reference.isLocal()
    method = getattr(reference.value, methodName)
    return method(*args, **kw)

def send(reference, methodName, args, kw):
    '''only send the calls to the object.
Nothing is returned, No Errors handled.'''
    reference.process.call(_send_execute, (reference, methodName, args, kw))

#
# proxy methods for asynchronous send and receive 
#

class Result(ApplyResult):

    def __init__(self, callback = None):
        ApplyResult.__init__(self, {}, callback)
        
    def setValue(self, value):
        self._set(None, (True, value))

    def setError(self, ty, err, tb):
        self.error = (ty, err, tb)
        self._set(None, (False, err))

def _async_execute(resultReference, reference, methodName, args, kw):
    try:
        result = _send_execute(reference, methodName, args, kw)
        send(resultReference, 'setValue', (result,), {})
    except:
        ty, err, tb = sys.exc_info()
        ## todo: include traceback
        send(resultReference, 'setError', (ty, err, None), {})
    

def async(reference, methodName, args, kw, callback = None):
    '''call the methods of the object.
returns a Result object.'''
    result = Result(callback)
    resultReference = objectbase.store(result)
    args = (resultReference, reference, methodName, args, kw)
    reference.process.call(_async_execute, args)
    return result

#
# proxy methods for synchronous send and receive
#

def sync(*args):
    '''synchonously call the methods of the object.
This is the typical communication of python.
It can make the program slow.'''
    result = async(*args)
    return result.get()

#
# proxy methods for callback communication
#

def callback(reference, methodName, args, kw):
    '''call the methods of the object but pass a callback as first argument
this callback receives the result.get() if no error occurred'''
    assert args, 'the callback must be the first argument'
    assert callable(args[0]), 'the callback must be the first argument'
    callback = args[0]
    methodArgs = args[1:]
    return async(reference, methodName, methodArgs, kw, callback = callback)


#
# creating references
#

def reference(obj, method, ProxyClass = Proxy):
    '''reference an object and adapt communication to the method
the object can also be a Reference. So the method can be changed'''
    if ProxyClass.isProxy(obj):
        reference = insideProxy(obj).getReference()
    else:
        reference = objectbase.store(obj)
    return ProxyClass(method, reference)
        
__all__ = ['reference', 'callback', 'sync', 'async', 'send', 'Proxy']