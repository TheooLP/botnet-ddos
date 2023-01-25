#!/usr/bin/python3

import socket
import sys
import os
from threading import Thread

class Server:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 12345
        self.socket = None
        self.all_connections = []
        self.all_addresses = []
        self.number_of_clients = 0

        # Threads to handle each client
        self.threads = []

        self._create_socket()
        self._bind_socket()

    def _create_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except socket.error as msg:
            print("Socket creation error: " + str(msg))
            sys.exit(1)

    def _bind_socket(self):
        try:
            print("Binding the Port: " + str(self.port))
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
        except socket.error as msg:
            print("Socket binding error: " + str(msg))
            sys.exit(1)

    def accept_connections(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                conn.setblocking(1)
                self.all_connections.append(conn)
                self.all_addresses.append(addr)
                self.number_of_clients += 1
                print("[+] New client connected: " + addr[0])
            except:
                print("Error accepting connections")
                sys.exit(1)

    def start(self):
        # Create a thread to accept connections
        accept_thread = Thread(target=self.accept_connections, name='accept_thread')
        accept_thread.start()
        # add the thread to the list of threads
        self.threads.append(accept_thread)

if __name__ == "__main__":
    server = Server()
    server.start()
