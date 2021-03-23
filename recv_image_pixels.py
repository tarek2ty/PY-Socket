from fl_networking_tools import ImageViewer
import socket
import pickle

viewer = ImageViewer()
#viewer.start()
udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(("0.0.0.0",20001))

def get_pixels():
    while True:
        data, client_add = udp_server.recvfrom(1024)
        message = pickle.loads(data)
        pos = message[0]
        rgb = message[1]
        viewer.put_pixel(pos, rgb)
viewer.start(get_pixels)