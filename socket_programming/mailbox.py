# /code_practice/socket_programming/mailbox.py

import pytest
import unittest
import time 
from dataclasses import dataclass, field

from bounded_fifo_queue import BoundedQueue, FullQueueError, EmptyQueueError

class MailboxFullError(Exception):
    pass

class MailboxEmptyError(Exception):
    pass

@dataclass
class Envelope:
    payload: str
    sender_id: str = field(default_factory=str) 
    timestamp: float = field(default_factory=time.time)

class Mailbox:
    def __init__(self, capacity: int):
        self._capacity = capacity 
        self._mailbox:BoundedQueue = BoundedQueue(self._capacity)

    def __len__(self):
        return len(self._mailbox)

    def send(self, payload: str, sender_id: str = None):
        envelope = Envelope(payload=payload, sender_id=sender_id)

        try:
            self._mailbox.push(envelope)
        except FullQueueError:
            raise MailboxFullError("Mailbox full. Read a few messages or try again later.")

    def receive(self) -> Envelope:
        try:
            envelope = self._mailbox.pop() 
        except EmptyQueueError:
            raise MailboxEmptyError("No messages in this mailbox.")
        return envelope

    def peek(self):
        try:
            envelope = self._mailbox[0]
        except EmptyQueueError:
            raise MailboxEmptyError("No messages in this mailbox.")
        return envelope

    def __iter__(self):
        return iter(self._mailbox)

    def __next__(self):
        return next(self._mailbox)

class TestMailbox(unittest.TestCase):
    def test_send_and_receive_envelope(self):
        mbox = Mailbox(capacity=5)
        mbox.send(payload="INIT_AGENT", sender_id="system")
        
        self.assertEqual(len(mbox), 1)
        envelope = mbox.receive()
        
        self.assertEqual(envelope.payload, "INIT_AGENT")
        self.assertEqual(envelope.sender_id, "system")
        self.assertIsInstance(envelope.timestamp, float)
        self.assertEqual(len(mbox), 0)

    def test_peek(self):
        mbox = Mailbox(capacity=5)
        mbox.send("PING", sender_id="node_1")

        # Peek inspects without popping
        envelope = mbox.peek()
        self.assertIsNotNone(envelope)
        self.assertEqual(envelope.payload, "PING")
        self.assertEqual(len(mbox), 1)

        # Confirm item is still there for receive()
        popped = mbox.receive()
        self.assertEqual(popped.payload, "PING")
        self.assertEqual(len(mbox), 0)

    def test_peek_empty(self):
        mbox = Mailbox(capacity=5)
        self.assertIsNone(mbox.peek())

    def test_mailbox_full_and_empty_errors(self):
        mbox = Mailbox(capacity=1)
        mbox.send("MSG_1")

        with self.assertRaises(MailboxFullError):
            mbox.send("MSG_2")

        mbox.receive()

        with self.assertRaises(MailboxEmptyError):
            mbox.receive()


if __name__ == "__main__":
    unittest.main()

