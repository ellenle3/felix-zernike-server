#!/usr/bin/env python3

'''
fwfstool is the user interface, takes in the parameters, passes those down to handling functions
for calculating the zernike variables.
'''


# System imports
import argparse
import sys
import numpy as np
from datetime import datetime
import socket
import logging

# Local import
from Destination import Destination
from SpotFile import SpotFile
from Spot import Spot

import image as image

from FelixSpotDetector import FelixSpotDetector

#defaults
input_file = SpotFile("data", "wfs.fits", 0, 0, 512, 512)
calibration_file = SpotFile("data", "cal.fits", 0, 0, 512, 512)
destination = Destination.HEXE

input_center = Spot(-1, -1) # This contains the return value to be passed back for guiding


logging.basicConfig(level=logging.DEBUG)

#functions
class Fwfstool:
    def print_parameters(self):
        print(f"\tinput filename:".ljust(30) + input_file.filename)
        print(f"\tinfile startx:".ljust(30) + str(input_file.startx))
        print(f"\tinfile starty:".ljust(30) + str(input_file.starty))
        print(f"\tinfile width:".ljust(30) + str(input_file.width))
        print(f"\tinfile height:".ljust(30) + str(input_file.height))
        print()
        print(f"\tcalibration filename:".ljust(30) + calibration_file.filename)
        print(f"\tcalibration startx:".ljust(30) + str(calibration_file.startx))
        print(f"\tcalibration starty:".ljust(30) + str(calibration_file.starty))
        print(f"\tcalibration width:".ljust(30) + str(calibration_file.width))
        print(f"\tcalibration height:".ljust(30) + str(calibration_file.height))
        print()
        print(f"\tdestination:".ljust(30) + str(destination.name))


    def send_string_tcp(self, host, port, message):
    # Create a TCP/IP socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Connect to the server
            s.connect((host, port))
            
            # Send the message
            s.sendall(message.encode())
            
            # Receive the response from the server
            response = s.recv(1024).decode()  # Buffer size is 1024 bytes
            print("Received:", response)


    def send_string_udp(self, host, port, message):
    # Create a UDP/IP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Send the message
            s.sendto(message.encode(), (host, port))
            
            # Receive the response from the server
            response, _ = s.recvfrom(1024)  # Buffer size is 1024 bytes
            print("Received:", response.decode())


        #main
    def main(self, cmdline):
        print("Parameter string:")
        print(cmdline)

        parser = argparse.ArgumentParser(description='FELIX WFS Tool')
        parser.add_argument('-v', '--version', action='store_true', help='Show version information and exit')
        parser.add_argument('-i', '--infile', help='Input file')
        parser.add_argument('-w', '--window', help='Window position and size')
        parser.add_argument('-c', '--calfile', help='Calibration file')
        parser.add_argument('-r', '--calwindow', help='Calibration window position and size')
        # parser.add_argument('-s', '--instrument', help='Instrument name')
        parser.add_argument('-d', '--destination', help='Hexe, Chop, or ASM')

        cmd_args = cmdline.split()
        args = parser.parse_args(cmd_args)

        if args.version:
            print("FELIX WFS Tool Version 0.10")
            exit(0)

        print("FELIX WFS Tool")

        if args.infile:
            input_file.filename = args.infile

        if args.window:
            wstr = args.window.split(",")
            input_file.startx = int(wstr[0])
            input_file.starty = int(wstr[1])
            input_file.width =  int(wstr[2])
            input_file.height = int(wstr[3])

        if args.calfile:
            calibration_file.filename = args.calfile
            

        if args.calwindow:
            cstr = args.calwindow.split(",")
            calibration_file.startx = int(cstr[0])
            calibration_file.starty = int(cstr[1])
            calibration_file.width =  int(cstr[2])
            calibration_file.height = int(cstr[3])

        if args.destination:
            dest = args.destination
            if dest == "hexe":
                destination = Destination.HEXE
            elif dest == "chop":
                destination = Destination.CHOP
            elif dest == "asm":
                destination = Destination.ASM
            else:
                print("Invalid destination, defaulting to hexe")
                destination = Destination.HEXE

        self.print_parameters()

        # Step one, find the center of the input file to pass back for the guider
        # note: we do this now, before we rotate and offset, so we can get the unmodified values
        # that the guider will use.  We will not do the same for the calibration file

        felix_spot_detector = FelixSpotDetector()

        '''
        Get the input file data, find the five points (center and spots), save the center for passing back
        for the guider.  Computationally not great, but not a huge hit.
        '''
        print("\n\n***** Guide Center *****")
        input_data = felix_spot_detector.get_data(input_file)
        _, guide_center, _ = felix_spot_detector.detect_spots(input_file, input_data)
        print("Input Center for Guider: " + str(guide_center[0]) + ", " + str(guide_center[1]));


        print("\n\n***** Get calibration and input position locations *****")

        calibration_data = felix_spot_detector.get_data(calibration_file)
        some_data, calibration_center, calibration_points = felix_spot_detector.detect_spots(calibration_file, calibration_data)
        print("Calibration Center: " + str(calibration_center[0]) + ", " + str(calibration_center[1]));


        input_data = felix_spot_detector.get_data(input_file)
        input_data, input_center, input_points = felix_spot_detector.detect_spots(input_file, input_data)
        image.write_gsdata_as_png("debug/input1.png", image.fits2numpy(input_data))


        print("\nsend point data to zernike server")
        # create timestamp
        zs_command = "points [" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] "

        point_list = str(input_center[0]) + "," + str(input_center[1]) + ","

        for iii in range(4):
            point_list += str(input_points[iii][0]) + "," + str(input_points[iii][1])
            point_list += ","

        point_list += str(calibration_center[0]) + "," + str(calibration_center[1]) + ","

        for iii in range(4):
            point_list += str(calibration_points[iii][0]) + "," + str(calibration_points[iii][1])
            if iii < 3:
                point_list += ","

        zs_command += " [" + point_list + "]"

        logging.debug(zs_command)

        # send the command to the server
        #self.send_string_udp('127.0.0.1', 8000, zs_command)


        # Now compute the focus for the hexe





def mymain():
    # hack up the command line to be a string of arguments passed to the commanline
    cmdline = ""
    cmdline = cmdline + " ".join(sys.argv[1:])
    #print(cmdline)
    # run the tool on the parameters given
    fwfstool = Fwfstool()
    fwfstool.main(cmdline)

#mymain()
