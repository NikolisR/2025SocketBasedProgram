import socket
from serverConstants import MYIPADDRESS, PORT

# this sets up the socket connection and binds the right port to the ip. It will then listen so that it can catch and redirect here.
def setup():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((MYIPADDRESS, PORT))
    server.listen()
    server.setblocking(False)
    print(f"[+] Server listening on {MYIPADDRESS}:{PORT}")
    return server
