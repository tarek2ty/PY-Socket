import socket

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(('0.0.0.0',20001))
data, client_address = udp_server.recvfrom(1024)
mess = data.decode()
print (mess)

parts = mess.split(",")
print(parts)

