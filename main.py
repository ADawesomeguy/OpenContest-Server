import socket

s = socket.socket()

s.bind(('127.0.0.1', 6000))

s.listen(5)
print("socket is listening")

while True:
    # Establish connection with client
    c, addr = s.accept()
    print('Received connection from', addr)
    
    # Close the connection with the client
    c.close()
