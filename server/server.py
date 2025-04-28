from serverSocketHandler import setup
from gameHandling import runner

if __name__ == "__main__":
    server = setup()
    runner(server)
