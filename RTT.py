from scapy.all import *
from datetime import datetime

pcap_file=("out/cqi_4_ms/mypcapfile-5-1.pcap")
ti = datetime.now()


# Read the pcap file
packets = rdpcap(pcap_file)


# Dictionary to store packet timestamps
packet_timestamps = {}

# Iterate over each packet
for packet in packets:
    if packet.haslayer(TCP):
        seq_num = packet[TCP].seq
        ack_num = packet[TCP].ack
        timestamp = packet.time
        if seq_num not in packet_timestamps:
            packet_timestamps[seq_num] = timestamp
        else:
            rtt = timestamp - packet_timestamps[seq_num]
            print(f"Sequence Number: {seq_num}, Acknowledgment Number: {ack_num}, RTT: {rtt} seconds")

tf = datetime.now()
print(" ")
print(tf-ti)

