#!/usr/bin/env python3
#
########################################################################
# Copyright (C) 2014 Mark J. Blair, NF6X
#
# This file is part of papertape
#
#  papertape is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  papertape is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with py  If not, see <http://www.gnu.org/licenses/>.
########################################################################


"""Send tape to reader/punch over serial interface."""


import sys
import signal
import serial
import argparse
import textwrap
import papertape
import time
import socket

# Main entry point when called as an executable script.
if __name__ == '__main__':

    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(
        prog='tapeout.py',
        description=textwrap.dedent("""\
        Punched paper tape writer utility version {:s}
          {:s}
          {:s}
          {:s}\
        """.format(papertape.__version__, papertape.__copyright__,
                       papertape.__pkg_url__, papertape.__dl_url__)),
        add_help=True,
        formatter_class=argparse.RawDescriptionHelpFormatter)


    parser.add_argument('--baud', action='store', nargs=1,
                        metavar='BAUD', default=[4800], type=int,
                        help="""Specify baud rate for tape punch output.
                        Defaults to 4800.""")

    parser.add_argument('port', action='store', nargs=1,
                        metavar='PORT',
                        help='Serial port or network port for tape punch output.')

    parser.add_argument('file', action='store', nargs=1,
                        metavar='FILENAME',
                        help='Input file name.')

    parser.add_argument('--ipaddr', action='store', nargs=1,
                        metavar='IPADDR', type=str, 
                        help='IP address')



    # Parse the command-line arguments.
    args = parser.parse_args()


    # Open the tape punch serial port.
    if(args.ipaddr[0] == ""):
        try:
            punch = serial.Serial(port=args.port[0], baudrate=args.baud[0],
                              bytesize=serial.EIGHTBITS,
                              parity=serial.PARITY_NONE,
                              timeout=None, write_timeout=None,
                              xonxoff=False, rtscts=True, dsrdtr=False)
        except:
            print(punch)
            print('Error opening port.')
    else:
        punch = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        myip = args.ipaddr[0]
        myport = int(args.port[0])
        print("connecting to:",myip, myport)
        try:
            punch.settimeout(10)
            punch.connect((myip, myport))
        except:
            print("Couldnt connect with the socket-server: %s\n" % punch.error)

    
    infile = open(args.file[0], 'rb')

    count = 0
    readeron = "\x11"
    punchon = "\x12"
    readeroff = "\x13"
    punchoff = "\x14"
    escapech = "\x1B"
    whatami = "\x93"
    dubf = b'\xff'
    wtfman = b'\xA6'

    print("Turning on punch \n")
    if(args.ipaddr[0] == ""):
        punch.write(bytes(punchon[0], "utf-8"))
    else:
        punch.send(bytes(punchon[0], "utf-8"))
    time.sleep(2)
    for c in infile.read():
        if(args.ipaddr[0] == ""):
            if(c == readeron[0] or c == punchon[0] or c == readeroff[0] or c == punchoff[0] or c == escapech[0] or c == whatami[0]):
                punch.write(bytes(escapech[0], "utf-8"))
                print("wrote esc char\n")
            punch.write(bytes([c]))
        else:
#            if(bytes([c]) == bytes(readeron[0], "utf-8") or bytes([c]) == bytes(punchon[0], "utf-8") or bytes([c]) == bytes(readeroff[0], "utf-8") or bytes([c]) == bytes(punchoff[0], "utf-8")):
#                punch.send(bytes(escapech[0], "utf-8"))
#                print("\nwrote esc char")
#            if(bytes([c]) == bytes(escapech[0], "utf-8") or bytes([c]) == bytes(whatami[0], "utf-8")):
#                punch.send(bytes(escapech[0], "utf-8"))
#                print("\nwrote esc char")
            if(bytes([c]) == dubf):
                print("\ndubf")
                punch.send(dubf)
            elif(bytes([c]) == wtfman):
                print("\nNOT escaping")
            else:
                print("\nescape")
                punch.send(bytes(escapech[0], "utf-8"))
            punch.send(bytes([c]))
        sys.stdout.write('{:02X} '.format(c))
        if (count % 16) == 15:
            sys.stdout.write('\n')
        count = count + 1
        sys.stdout.flush()
        # Hack to work around apparently broken flow control
        time.sleep(0.1)
        
    sys.stdout.write('\n')
    print("Stopping punch")
    if(args.ipaddr[0] == ""):
        punch.write(bytes(punchoff[0], "utf-8"))
    else:
        print("sending char")
        punch.send(bytes(punchoff[0], "utf-8"))

    punch.close()
