import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
message = "Hello, World!"
data = message.encode()
address = ('127.0.0.1', 20001)
client_socket.sendto(data, address)

data1, address1 = client_socket.recvfrom(1024)
mess = data1.decode()
print(mess)