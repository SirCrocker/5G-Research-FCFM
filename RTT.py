from scapy.all import *
import csv

def get_RTT(pcap_filename):

    # Read the pcap file
    packets = rdpcap(pcap_filename)

    # Dictionary to store packet timestamps, rtt's and ack's received
    packet_timestamps = {}
    rtt_dict = {}
    ack_received = []

    # Iterate over each packet
    for packet in packets:
        if packet.haslayer(TCP):

            seq_num = packet[TCP].seq
            ack_num = packet[TCP].ack
            timestamp = packet.time
            TCP_payload = len(packet[TCP].payload)

            # Cases to skip
            case_1 = (seq_num == 0) # SYN
            case_2 = (seq_num == 1 and ack_num == 1 and TCP_payload == 0) # SYN, ACK
            case_3 = (ack_num in ack_received) # DUP ACK
            skip_packets = (case_1 or case_2 or case_3)

            if skip_packets:
                continue

            # Add timestamp of sending packet
            if seq_num not in packet_timestamps:
                packet_timestamps[seq_num] = timestamp
                rtt_dict[seq_num] = 0

            # Get Sequence Number from ACK
            recovered_seq_num = ack_num-1448
            
            # Check if a packet is ACK and the SEQ exists
            if (seq_num == 1) and  (recovered_seq_num in packet_timestamps):
                rtt = timestamp - packet_timestamps[recovered_seq_num]
                rtt_dict[recovered_seq_num] = rtt*1000
                ack_received.append(ack_num)

    # for seq in rtt_dict:
    #     n_packet = int((seq-1)/1448 + 1)
    #     if rtt_dict[seq] > 0:
    #         print(f"El paquete N°{n_packet} de Sequence Number: {seq}, RTT: {rtt_dict[seq]} milliseconds")
    #     else:
    #         print(f"El paquete N°{n_packet} de Sequence Number: {seq} se perdió :(")

    # File path to save the CSV
    file_path = 'RTT.csv'

    # Open the CSV file in write mode
    with open(file_path, 'w', newline='') as file:

        # Create a CSV writer
        writer = csv.writer(file, delimiter=';')

        # Write the header
        writer.writerow(["Sequence number", "Packet Number", "RTT [ms]"])

        # Write data rows
        for seq, rtt in rtt_dict.items():
            n_packet = int((seq-1)/1448 + 1)
            writer.writerow([seq, n_packet, rtt])

    print("CSV file has been written successfully.")