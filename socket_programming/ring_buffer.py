import unittest

class BufferFullError(Exception):
    """Raised when writing to a full ring buffer."""
    pass

class BufferEmptyError(Exception):
    """Raised when reading from an empty ring buffer."""
    pass

class RingBuffer:
    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Ring buffer capacity must be a positive integer.")

        self.capacity = capacity
        self._buf = [None] * self.capacity
        self._head = 0  # Write index
        self._tail = 0  # Read index
        self._size = 0  # Current number of items stored
     
    def __len__(self) -> int:
        """Returns the current number of items stored (enables len(buf))."""
        return self._size

    def __repr__(self) -> str:
        """Provides a clear debugging string representation."""
        return f"RingBuffer(capacity={self.capacity}, size={self._size})"

    def write(self, item, overwrite: bool = False) -> None:
        """Write an item at the head position and advance head.
           Optionally, overwrite oldest if buffer is full and overwrite=True.
        """ 
        if self._size >= self.capacity:
            if overwrite:
                # Advance tail to discard the oldest item
                self._tail = (self._tail + 1) % self.capacity
                self._size -= 1
            else:
                raise BufferFullError("The buffer is full. Call buffer.read().")

        self._buf[self._head] = item
        self._head = (self._head + 1) % self.capacity
        self._size += 1

    def read(self):
        """Read and return item from tail position and advance tail."""
        if self._size == 0:
            raise BufferEmptyError("The buffer is empty. Call buffer.write(item).")

        item = self._buf[self._tail]
        self._buf[self._tail] = None
        self._tail = (self._tail + 1) % self.capacity
        self._size -= 1
        return item

    def available_read(self) -> int:
        """Returns how many items are available to read."""
        return self._size

    def available_write(self) -> int:
        """Returns how much space is left to write."""
        return self.capacity - self._size


class TestRingBuffer(unittest.TestCase):
    def test_initial_state(self):
        buf = RingBuffer(3)
        self.assertEqual(buf.available_read(), 0)
        self.assertEqual(buf.available_write(), 3)

    def test_single_write_and_read(self):
        buf = RingBuffer(3)
        buf.write("A")
        self.assertEqual(buf.available_read(), 1)
        self.assertEqual(buf.available_write(), 2)
        self.assertEqual(buf.read(), "A")
        self.assertEqual(buf.available_write(), 3)
        self.assertEqual(buf.available_read(), 0)

    def test_buffer_full_error(self):
        buf = RingBuffer(2)
        buf.write("A")
        buf.write("B")
        self.assertEqual(buf.available_write(), 0)
        with self.assertRaises(BufferFullError):
            buf.write("C")

    def test_buffer_empty_error(self):
        buf = RingBuffer(2)
        self.assertEqual(buf.available_read(), 0)
        with self.assertRaises(BufferEmptyError):
            buf.read()

    def test_pointer_wrap_around(self):
        """Verifies head and tail wrap around indices correctly using modulo."""
        buf = RingBuffer(3)
        
        # Fill buffer: slots [0, 1, 2]
        buf.write(1)
        buf.write(2)
        buf.write(3)
        
        # Read two items: tail moves to index 2
        self.assertEqual(buf.read(), 1)
        self.assertEqual(buf.read(), 2)
        
        # Write two items: head should wrap around back to index 0 and 1
        buf.write(4)
        buf.write(5)
        
        # Read remaining items in FIFO order
        self.assertEqual(buf.read(), 3)
        self.assertEqual(buf.read(), 4)
        self.assertEqual(buf.read(), 5)
        self.assertEqual(buf.available_read(), 0)

    def test_fill_and_empty_repeatedly(self):
        """Tests continuous stream simulation without reallocating underlying list."""
        buf = RingBuffer(2)
        for i in range(10):
            buf.write(i)
            self.assertEqual(buf.read(), i)
        self.assertEqual(buf.available_read(), 0)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            RingBuffer(0)
        with self.assertRaises(ValueError):
            RingBuffer(-5)

    def test_len_dunder(self):
        buf = RingBuffer(5)
        self.assertEqual(len(buf), 0)
        buf.write("X")
        self.assertEqual(len(buf), 1)

    def test_overwrite_behavior(self):
        # Testing optional overwrite feature if implemented
        buf = RingBuffer(2)
        buf.write("A")
        buf.write("B")
        buf.write("C", overwrite=True)  # Overwrites 'A'
        
        self.assertEqual(buf.read(), "B")
        self.assertEqual(buf.read(), "C")

if __name__ == "__main__":
    unittest.main()
