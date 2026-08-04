# /code_practice/socket_programming/async_loop.py

import socket

from future import Future
from event_loop_dispatcher import EventLoopDispatcher
from task_scheduler import TaskScheduler
from framed_socket import send_frame, recv_frame

class ChatClient:
    def __init__(self, sock:socket.socket, dispatcher:EventLoopDispatcher, scheduler:TaskScheduler):
        self.sock = sock
        self.dispatcher = dispatcher
        self.scheduler = scheduler
        self.printed_messages = []

    def send_message(self, message: str):
        send_frame(self.sock, bytes(message, "utf-8"))

        coro = self.recv_message()
        future = next(coro)
        def resume_recv_message(fut):
            client_sock = fut.result()
            try:
                coro.send(client_sock)
            except StopIteration:
                pass
        future.add_done_callback(resume_recv_message)
     
        self.dispatcher.register(self.sock, future.set_result)

    def recv_message(self, *args):
        client_sock = yield Future()
        try:
            message = recv_frame(client_sock)
        except ConnectionError as e:
            print(e)
        else:
            self.scheduler.spawn(self.print_message, message, task_id="client_print_message")

    def print_message(self, message: str):
        self.printed_messages.append(message)

