import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(('127.0.0.1', 8080))
print("connected")

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

# for message in recv_text(client):
#     print(message)                      #prints all the messages the generator receives

message = next(recv_text(client))     #prints next message where the generator has stopped
message2 = next(recv_text(client))
print(message)
print(message2)
client.close()