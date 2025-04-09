import sys
import argparse
import socket

HOST = '0.0.0.0'
PORT = 10488

def main(coords):

    message = "felixdata "

    for arg in coords:
        message += str(arg) + ", "
    
    # Remove last comma and space
    message = message[:-2]
    print(message)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Connect to the server
        s.connect((HOST, PORT))
        
        # Send the message
        s.sendall(message.encode())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send FELIX data to a socket')
    parser = argparse.ArgumentParser(description="FELIX slopes to Zernikes server")
    parser.add_argument("coords", type=float, nargs=8, help="Spot positions: x1 y1 x2 y2 x3 y3 x4 y4")
    args = parser.parse_args()

    main(args.coords)