import fl_networking_tools
from PIL import Image
import socket
import pickle
from time import sleep



image = Image.open("snail.bmp")

width, height = image.size
# So we can loop through every pixel
print(width, height)


udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for y in range(height):
    for x in range(width):
        pos = (x , y)                   # the position of the pixel
        rgb = image.getpixel(pos)       # the color of this pixel (rgp)
        message = (pos, rgb)
        data = pickle.dumps(message)
        udp_client.sendto(data, ("127.0.0.1", 20001))
        sleep(0.001)           # we may experience major losses becuase of speed
                                # so we add a little waiting

# this info tells us every pos and its color
# for every pixel, we send its position and the color for when it's reconstructed
# which is not efficient
# many packets will be lost but we still recognize the image
# we convert the message into bytes using pickle
