import socket

PORT = 5555                                                                                                             # Server Port
BUFFER_SIZE = 4096                                                                                                      # 4KB readable for start, answers, names

# this does the socket handshake where it tells what port to ping to on the ipaddress you are joining
def serverConnection(ip_address, name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip_address, PORT))
    sock.sendall(name.encode())
    return sock
