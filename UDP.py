import socket

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Datagram instead of stream; udp instead of tcp

udp_server.bind(('0.0.0.0',20001))

data, client_address = udp_server.recvfrom(1024)
# since there is no connection socket, the recvfrom returns the address
# of the sender
# 1024 buffer size. this should be large enough to receive a whole packet
mess = data.decode()
print(mess)
mess2= mess+ "20"
data2=mess2.encode()
udp_server.sendto(data2, client_address)