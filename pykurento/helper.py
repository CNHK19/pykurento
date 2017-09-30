from functools import wraps
from time import time

def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        print ('took: %2.4f sec, func:%r args:[%r, %r] '% (te-ts, f.__name__, args, kw))
        return result
    return wrap
