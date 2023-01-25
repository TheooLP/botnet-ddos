#!/usr/bin/python3

import socket
import sys

class Server:
    def __init__(self):
        self.host = ''
        self.port = 12345
        self.socket = None
        self.all_connections = []
        self.all_addresses = []

    
