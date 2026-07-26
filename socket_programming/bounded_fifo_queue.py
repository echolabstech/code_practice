from collections import deque
import pytest

class FullQueueError(Exception):
    """Raised when trying to push to a full queue."""
    pass

class EmptyQueueError(Exception):
    """Raised when trying to pop from an empty queue."""
    pass

class BoundedQueue:
    def __init__(self, max_size: int):
        self.max_size = max_size
        self._storage = deque([])

    def push(self, item: None) -> None:
        """Add an item to the back of the queue. Throw error if full."""
        if len(self._storage) >= self.max_size:
            raise FullQueueError(f"Queue max size reached: {self.max_size}.")
        self._storage.append(item) 

    def pop(self) -> None:
        """Remove and return an item from the front. Throw error if empty."""
        if len(self._storage) == 0:
            raise EmptyQueueError(f"Queue empty.")
        return self._storage.popleft()

    def is_full(self) -> bool:
        return len(self._storage) >= self.max_size

    def is_empty(self) -> bool:
        return len(self._storage) == 0

    def __len__(self) -> int:
        return len(self._storage) 

if __name__ == "__main__":
    queue = BoundedQueue(1)

    queue.push(1)
    assert queue.is_full() == True
    queue.pop()
    assert queue.is_empty() == True

    with pytest.raises(EmptyQueueError):
        queue.pop()

    queue.push(1)

    with pytest.raises(FullQueueError):
        queue.push(2)

