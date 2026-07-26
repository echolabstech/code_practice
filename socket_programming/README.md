# socket programming

Here we experiment with low level socket servers and clients. We write our own servers by creating sockets, managing read and write socket states, reading and writing from / to sockets, formatting and validating data for layer 5-6 standardized protocols (i.e. http) and custom protocols (i.e. custom chat server). 

## How to test

### text_chat_server.py

curl -d "foo" http://localhost:8080

### how_to_use_event_write.py

nc localhost 9000

