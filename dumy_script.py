import socket

def recv_text(recv_socket):
    buffer = ""                         #hold the received data
    socket_open = True                  #socket open
    while socket_open:
        data = recv_socket.recv(1024)   #receive data
        if not data:
            socket_open = False         #close socket if no data
        buffer += data.decode()         #add the received to the buffer
        index = buffer.find("\n")       #check if we have a complete message and what is its final index
                                        #true if > -1
        while index>-1:
            message = buffer[:index]
            buffer  = buffer[index+1:]
            yield message
            index = buffer.find("\n")

def send_text(send_socket, text):
    text+="\n"
    data=text.encode()
    send_socket.send(data)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('127.0.0.1',8080))
open_sock = True
while open_sock:
    send_text(client, "hello, world!!")
    mess = next(recv_text(client))
    print(">>>",mess)
    if mess == "end":
        open_sock = False
    if mess == "":
        print("*** NO messages!")
        open_sock = False

