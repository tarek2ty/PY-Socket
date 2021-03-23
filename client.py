import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(('127.0.0.1', 8080))
print("connected")

data = client.recv(1024)
# we use the client socket to manage the session
# 1024 is the buffer; which is the maximum amount of data to be received at once
# should be small powers of 2 (1024, 2048, 4096, ....)

message = data.decode()
# decode the data from the UTF-8
print (message)

message2= "client message!!"
data2= message2.encode()
client.send(data2)

client.close()

