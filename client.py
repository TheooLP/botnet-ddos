#!/usr/bin/python3

import socket
import sys
from threading import Thread

class Client:
    def __init__(self):
        self.host = "localhost"
        self.port = 12345
        self.socket = None

        # Connect to server
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            print("Socket creation error: " + str(msg))
            sys.exit(1)
        try:
            self.socket.connect((self.host, self.port))
        except socket.error as msg:
            print("Socket connection error: " + str(msg))
            sys.exit(1)

if __name__ == "__main__":
    client = Client()
