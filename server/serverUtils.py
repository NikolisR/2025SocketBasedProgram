def displayGUI(clients, msg: str):
    for s in list(clients):
        try:
            s.sendall(msg.encode())
        except:
            pass

def leaveEarlyHandler(s, clients, scores):
    if s in clients:
        del clients[s]
    if s in scores:
        del scores[s]
    try:
        s.close()
    except:
        pass
