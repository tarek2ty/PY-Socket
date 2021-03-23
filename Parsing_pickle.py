import socket
import time
import platform
import pickle


t = time.time()
netwok_name = platform.node()
version = platform.python_version_tuple()
all = (t , netwok_name , version)

data = pickle.dumps(all) #######
print(data)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.sendto(data, ("127.0.0.1",20001))