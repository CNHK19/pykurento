import threading

class CountDownLatch(object):
    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Condition()

    def countDown(self):
        self.lock.acquire()
        self.count -= 1
        if self.count <= 0:
            self.lock.notifyAll()
        self.lock.release()

    def await(self, timeout=None):
        self.lock.acquire()
        while self.count > 0:
            self.lock.wait(timeout)
        self.lock.release()