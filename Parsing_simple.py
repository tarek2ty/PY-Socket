# send different types of data to the other side
import socket
import time
#import os
#import sys
import platform
t = time.time()
#name = socket.gethostname()
#print(socket.gethostbyname("www.google.com"))
#vers= sys.version_info
netwok_name = platform.node()
netwok_name = "Tare,eek"
version = platform.python_version_tuple()
print(netwok_name, version)

#get all variables into one message

all = str(t) +","+ netwok_name+"," + version[0]+","+version[1]+","+version[2][0]
print(all)
data = all.encode()
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.sendto(data, ("127.0.0.1",20001))


