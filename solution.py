import socket
from socket import *
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8
MAX_HOPS = 30
TIMEOUT = 2.0
TRIES = 1
# The packet that we shall send to each router along the path is the ICMP echo
# request packet, which is exactly what we had used in the ICMP ping exercise.
# We shall use the same packet that we built in the Ping exercise

def checksum(string):
# In this function we make the checksum of our packet
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer

def build_packet():

    myChecksum = 0
    myid = os.getpid() & 0xFFFF
    header = struct.pack("bbHHh",ICMP_ECHO_REQUEST,0,myChecksum,myid,1)
    data = struct.pack("d",time.time())
    myChecksum = checksum(header + data)

    if sys.platform == "darwin":
        myChecksum = socket.htons(myChecksum) & 0xFFFF
    else:
        myChecksum = htons(myChecksum)

    header = struct.pack("bbHHh",ICMP_ECHO_REQUEST,0,myChecksum,myid,1)

    packet = header + data
    return packet

def get_route(hostname):
    timeLeft = TIMEOUT
    tracelist1 = [] #This is your list to use when iterating through each trace
    tracelist2 = [] #This is your list to contain all traces

    for ttl in range(1,MAX_HOPS):
        for tries in range(TRIES):
            destAddr = gethostbyname(hostname)

            icmp = getprotobyname("icmp")
            mySocket = socket(AF_INET,SOCK_RAW,icmp)

            mySocket.setsockopt(IPPROTO_IP, IP_TTL, struct.pack('I', ttl))
            mySocket.settimeout(TIMEOUT)
            try:
                d = build_packet()
                mySocket.sendto(d, (hostname, 0))
                t= time.time()
                startedSelect = time.time()
                whatReady = select.select([mySocket], [], [], timeLeft)
                howLongInSelect = (time.time() - startedSelect)
                if whatReady[0] == []: # Timeout
                    tracelist1.append("* * * Request timed out.")
                    tracelist2.append(tracelist1)
                recvPacket, addr = mySocket.recvfrom(1024)
                timeReceived = time.time()
                timeLeft = timeLeft - howLongInSelect
                if timeLeft <= 0:
                    tracelist1.append("* * * Request timed out.")
                    tracelist2.append(tracelist1)
            except timeout:
                continue

            else:
                hostAddr = str(socket.inet_ntoa(recvPacket[12:16]))
                recPacket, addr = mySocket.recvfrom(1024)
                types, code, checksum, id, sequence = struct.unpack('bbHHh', recPacket[20:28])

                try: #try to fetch the hostname
                    hostname = gethostbyaddr(hostAddr)
                except herror:   #if the host does not provide a hostname
                    hostname = "hostname not returnable"

                if types == 11:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 +
                    bytes])[0]
                    #You should add your responses to your lists here
                    tracelist1.append(str(ttl))
                    tracelist1.append("*")
                    tracelist1.append("request timed out")
                    tracelist2.append(tracelist1)

                elif types == 3:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    #You should add your responses to your lists here
                    tracelist1.append(str(ttl))
                    tracelist1.append("*")
                    tracelist1.append("destination host unreachable")
                    tracelist2.append(tracelist1)

                elif types == 0:
                    bytes = struct.calcsize("d")
                    timeSent = struct.unpack("d", recvPacket[28:28 + bytes])[0]
                    #You should add your responses to your lists here and return your list if your destination IP is met
                    tracelist1.append(str(ttl))
                    rtt = (timeSent - timeReceived) * 1000
                    tracelist1.append(str(rtt) + "ms")
                    tracelist1.append(str(destAddr))
                    tracelist1.append(hostname)
                    tracelist2.append(tracelist1)

                else:
                    #If there is an exception/error to your if statements, you should append that to your list here
                    tracelist1.append("* * * Error")
                    tracelist2.append(tracelist1)
                break
            finally:
                mySocket.close()

