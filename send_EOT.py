import socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("0.0.0.0", 8080))
server.listen(0)
print("waiting")

connect, add = server.accept()
print("connected")
def send_text(send_socket, text):
    text+="\n"
    data=text.encode()
    send_socket.send(data)
# We created an EOT character \n to know where the message ends
# def recv_text(recv_socket):
#     buffer = ""                         #hold the received data
#     socket_open = True                  #socket open
#     while socket_open:
#         data = recv_socket.recv(1024)   #receive data
#         if not data:
#             socket_open = False         #close socket if no data
#         buffer += data.decode()         #add the received to the buffer
#         index = buffer.find("\n")       #check if we have a complete message and what is its final index
#                                         #true if > -1
#         while index>-1:
#             message = buffer[:index]
#             buffer  = buffer[index+1:]
#             yield message
#             index = buffer.find("\n")


message = "thank you for connecting"
send_text(connect,message)
m="fight fight!"
send_text(connect,m)
connect.close()
server.close()