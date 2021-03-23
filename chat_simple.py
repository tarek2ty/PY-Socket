import socket

# we will receive a message and then input a message

choice = input("type s for server, c for client: ")

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

if choice == 's':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 8080))
    server.listen(0)
    print("waiting")
    connec , add = server.accept()
    print("connected")
elif choice == 'c':
    connec = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connec.connect(('127.0.0.1',8080))
else:
    print("NOT valid choice")

open_sock = True
while open_sock:
    mess = next(recv_text(connec))
    if mess == "":
        print("*** NO messages!")
        open_sock = False
    else:
        print(">>>", mess)
    send = input("send a message >>> ")
    if send == "" :
        open_sock = False
    else:
        send_text(connec, send)

connec.close()
server.close()