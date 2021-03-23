# if a pixel is received out of order, we consider it lost

from fl_networking_tools import ImageViewer
import socket
import pickle



viewer = ImageViewer()

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_server.bind(("0.0.0.0",20001))

def get_pixels():
    lost_pixels = 0         # will hold the number of lost pixels
    last_pixel = (-1, -1)   # last pixel that was updated
    viewer.text = lost_pixels  # write to the screen the lost pixels number
    while True:
        data, client_add = udp_server.recvfrom(1024)
        message = pickle.loads(data)
        pos = message[0]
        rgb = message[1]
        # check if new pos is larger than last pos in x or y more than one count
        # if yes that means that it's not the successor
        if (pos[0] - last_pixel[0] > 1) or (pos[1] - last_pixel[1] > 1):
            lost_pixels+=1              #increase the number of lost pixel
            viewer.text = lost_pixels
        last_pixel = pos                #the current pixel is pos recved
        viewer.put_pixel(pos, rgb)
viewer.start(get_pixels)
# the count will be 0 since we use the same device to communicate
