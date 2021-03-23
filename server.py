import socket
#the API for the socket to make python communicate
#with other apps

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#creat a socket server
#   AF_INET: IP socket
#   SOCK_STREAM: TCP socket

server.bind(("0.0.0.0", 8080))
#bind this server to an ip address and a port
#this address must be existing in the machine; we are not creating a new interface
#we are just binding our socket to an interface.
#   0.0.0.0 means it will pick up any connection at any ip add at this device
#   at port 8080; which is typically used for testing

server.listen(0)  # the 0 is the number of unaccepted connections the system will allow
                  # before refusing new ones
#our server listens to any connection

print("waiting for connection")

connection, address = server.accept()
#this new socket will result in two parameters;
#   the socket to the client
#   the address and the port of the client
print("connected")
print(connection)
print(address)