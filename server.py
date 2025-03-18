#!/usr/bin/env python3

import re
import argparse
import socket
import re
import argparse
from config import *

def process_command(command):
    # Define regex to match the command format: points [timestamp] [X1,Y1,X2,Y2,...X10,Y10]
    pattern = r"^points\s+\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]\s+\[([0-9.,\s\-]+)\]$"
    match = re.match(pattern, command.strip())

    if not match:
        return "Invalid command format!"

    # Extract the timestamp and the comma-separated values
    timestamp = match.group(1)  # The first capture group is the timestamp
    values_str = match.group(2)  # The second capture group is the values

    try:
        # Split the values and convert them to float
        values = [float(v) for v in values_str.split(',')]
    except ValueError:
        return "Error: Non-numeric value encountered in coordinates."

    if len(values) != 20:
        return "Error: Expected 10 pairs of X,Y values!"

    # Separate X and Y values
    X_values = values[::2]  # Every second value starting from 0 (X1, X2, ..., X10)
    Y_values = values[1::2]  # Every second value starting from 1 (Y1, Y2, ..., Y10)

    # Print the timestamp and the X,Y pairs neatly
    #print(f"Timestamp: {timestamp}")
    #for i in range(10):
    #    print(f"Pair {i + 1}: X = {X_values[i]}, Y = {Y_values[i]}")

    return timestamp, X_values, Y_values


def start_server_tcp(port):
    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))
        s.listen()

        print(f"TCP Server listening on {HOST}:{port}")

        while True:
            # Accept a connection
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                data = conn.recv(1024).decode()  # Receive and decode the incoming data

                if not data:
                    break

                print(f"Received command: {data}")

                # Process the received command
                result = process_command(data)

                if isinstance(result, tuple):       
                    timestamp, X_values, Y_values = result
                    response = f"Timestamp: {timestamp}\nX values: {X_values}\nY values: {Y_values}"
                    return timestamp, X_values, Y_values
                else:
                    response = result

                # Send back the response
                conn.sendall(response.encode())


def start_server_udp(port):
    # Create a UDP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((HOST, port))

        print(f"UDP server listening on {HOST}:{port}")

        while True:
            # Receive data from the client
            data, addr = s.recvfrom(1024)  # Buffer size is 1024 bytes
            data = data.decode()

            print(f"Received command from {addr}: {data}")

            # Process the received command
            result = process_command(data)

            if isinstance(result, tuple):
                timestamp, X_values, Y_values = result
                response = f"Timestamp: {timestamp}\nX values: {X_values}\nY values: {Y_values}"
                return timestamp, X_values, Y_values
            else:
                response = result  # This will be the error message

            # Send back the response to the client
            s.sendto(response.encode(), addr)


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Simple Server for Points Command (TCP/UDP)")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help="Port number to listen on")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Start the server using the specified or default port (UDP by default)
    start_server_tcp(args.port)
