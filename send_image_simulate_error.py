# we will use randint to randomly not send pixels
# so it's like an error
from PIL import Image
import socket
import pickle
from random import randint

image = Image.open("snail.bmp")
width, height = image.size
print(width, height)

####### send width over tcp #########
tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_client.connect(("127.0.0.1", 8081))
print("connected tcp to send the width!")
tcp_client.send(str(width).encode())
tcp_client.close()
####### you can comment out in both scripts later ########

udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
pixels_lost = 0

for y in range(height):
    for x in range(width):
        pos = (x , y)                   # the position of the pixel
        rgb = image.getpixel(pos)       # the color of this pixel (rgp)
        message = (pos, rgb)
        data = pickle.dumps(message)
        if randint(0,9) > 0:
            udp_client.sendto(data, ("127.0.0.1", 20001))
        else:
            pixels_lost += 1
print(pixels_lost)
