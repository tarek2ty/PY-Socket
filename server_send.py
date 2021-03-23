import socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("0.0.0.0", 8080))
server.listen(0)
print("waiting")

connect, add = server.accept()
# this socket will be used to send data
print("connected")
message = "thank you for connecting"
# We want to send this to the other side when it connects to us

data = message.encode()
# the message must be encoded to be sent to the other side
# this uses UTF-8
# we may use base64 for non text

connect.send(data)
#server sockets accepts and listens
#connection socket manages the session

# Change the client to see difference

data2=connect.recv(1024)
message2=data2.decode()
print(message2)
connect.close()
server.close()
#it's a good practice to close the socket to free system resources