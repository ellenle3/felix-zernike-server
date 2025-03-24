"""Script for recieving FELIX data through socket.
"""

import re
import argparse
import socket
import argparse
import numpy as np
from reconstruction import ZernikeReconstructor
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

def data_to_slopes(X_values, Y_values):
    """Converts data from socket to slopes for reconstructor. Calibration points
    are subtracted out.
    """
    # Expecting n_spots for the slopes + 1 for the coordinates of the central
    # spot. Mutliply by 2 for the cal data and input data.
    assert len(X_values) == 2 * (N_SPOTS + 1), f"X_values do not match n_spots={N_SPOTS}: {X_values}"
    assert len(Y_values) == 2 * (N_SPOTS + 1), f"Y_values do not match n_spots={N_SPOTS}: {Y_values}"

    # Index of X and Y values for input data
    idx_in = N_SPOTS + 1

    cal_points = np.array([X_values[:idx_in], Y_values[:idx_in]]).T
    input_points = np.array([X_values[idx_in:], Y_values[idx_in:]]).T

    # Get center points for subapertures using calibration data
    subap_centers = cal_points[1:] - cal_points[0]

    # If you don't want tip/tilt to be measured, replace cal_points[0] with
    # input_points[0] in the line below.
    input_slopes = input_points[1:] - cal_points[0] - subap_centers

    # Reformat to 1D array of x slopes then y slopes
    return np.array([input_slopes.T[0], input_slopes.T[1]]).flatten()


def print_color(s: str, c: str) -> None:
    """Prints a colored string.

    Parameters
    ----------
    s: str
        String to print.
    c: str 
        Color of the string. Options: 'red', 'green', 'yellow', 'blue',
        'magenta', 'cyan', 'black', 'white', 'bold', 'underline'

    Returns
    -------
    None
    """
    color_dict = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'black': '\033[30m',
        'white': '\033[37m',
        'bold':'\033[1m',
        'underline': '\033[4m'
    }
    assert c in color_dict, "The ANSI escape sequence for c must be defined print_color"

    color_code = color_dict[c]
    end_code = '\033[0m'
    print(f'{color_code}' + s + f'{end_code}')

def main(protocol, port):

    zernike_names = ["Tip", "Tilt", "Focus", "Astig1", "Astig2", "Coma1", "Coma2",
                      "Trefoil1", "Trefoil2", "Spherical"]

    # Initalize the wavefront reconstructor
    recon = ZernikeReconstructor()

    while True:

        # Start the server to listen for FELIX data
        if protocol == 'tcp':
            timestamp, X_values, Y_values = start_server_tcp(port)
        elif protocol == 'udp':
            timestamp, X_values, Y_values = start_server_udp(port)
        else:
            raise ValueError(f"Invalid protocol: {protocol}")

        slopes = data_to_slopes(X_values, Y_values)
        recon.update_slopes(slopes)
        a_z = recon.slopes_to_zernikes()
        
        for i, coeff in enumerate(a_z):
            prefix = f"  J = {i + 2}: "
            if coeff >= 0:
                prefix += ' '
            if i < 10:
                name = f" ({zernike_names[i]})"
            else:
                name = ''
            print_color(prefix + '{:.6f}'.format(coeff) + name, "cyan")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FELIX slopes to Zernikes server")
    parser.add_argument('--protocol', type=str, default='tcp', choices=['tcp', 'udp'], help="Protocol to use (tcp or udp)")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help="Port number to listen on")
    
    args = parser.parse_args()
    main(args.protocol, args.port)