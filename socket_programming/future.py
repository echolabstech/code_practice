# /code_practice/socket_programming/future.py

class Future:
    def __init__(self):
        self.callbacks = []
        self._result = None

    def add_done_callback(self, callback):
        if callback not in self.callbacks:
            self.callbacks.append(callback)

        if self._result:
            callback(self)

    def set_result(self, result):
        self._result = result

        for callback in self.callbacks:
            callback(self)

    def result(self):
        return self._result

