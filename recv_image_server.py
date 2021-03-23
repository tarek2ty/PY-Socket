import socket

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(("0.0.0.0", 20001))

while True:
    data, clien_address = udp_server.recvfrom(1024)
    print(data)