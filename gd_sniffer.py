#!/usr/bin/env python

import sys
import glob
import time
import ReadSerial
import serial

class GdSniffer():

    def __init__(self):

        self.init_serial()

    def init_serial(self):

        self.ports = self.serial_ports()
        print ("Serial ports with device connected are:", self.ports)

        print ('Identifying devices...')
        self.identify_device_ports()
        print ("Sam3U connected on port %s") % (self.sam3u_port)
        print ("Arduino Uno connected on port %s") % (self.uno_port)


    def identify_device_ports(self):
        self.statusPacket = None
        self.uno_port = None
        self.sam3u_port = None

        for i in self.ports:
            if self.uno_port != None and self.sam3u_port != None:
                break

            serial = ReadSerial.ReadSerial(i, self.parseStatusPacket)
            time.sleep(2)
            self.statusPacket = None
            self.sendChar(serial, 's')
            time.sleep(0.2)
            if self.statusPacket == "UNO\r":
                self.uno_port = i
            elif self.statusPacket == "SAM3U\r":
                self.sam3u_port = i
            serial.close()

        if self.uno_port != None:
            self.uno_serial = ReadSerial.ReadSerial(self.uno_port, self.parseUnoPacket)
        if self.sam3u_port != None:
            self.sam3u_serial = ReadSerial.ReadSerial(self.sam3u_port, self.parseSam3UPacket)


    def sendChar(self, serial, c):
        txPacket = bytearray()
        txPacket.extend(map(ord, c))
        serial.writeSerial(txPacket)

    def sendString(self, serial, packet):
        txPacket = bytearray()
        for i in range(0, len(packet)):
            txPacket.extend(map(ord, packet[i]))
        serial.writeSerial(txPacket)

    def serial_ports(self):
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def parseStatusPacket(self, packet):
        self.statusPacket = packet

    def tern2bin(self, ternary, opt):

        decimal = 0
        for i in range (0, len(ternary)):
            decimal += int(ternary[i]) * pow(3, len(ternary) - i - 1)
        decimal = int(decimal)

        if opt == 'dec':
            return '{:010d}'.format(decimal)        #decimal
        elif opt == 'bin':
            return '{:032b}'.format(decimal)       #binary
        elif opt == 'hex':
            return '{:08x}'.format(decimal)        #hex
        else:
            raise Exception('invalid option')

    def hex2tern(self, hexnum):
        decimal = 0
        for i in range (0, len(hexnum)):
            decimal += int(hexnum[i], 16) * pow(16, len(hexnum) - i - 1)
        decimal = int(decimal)
        ternValue = self.ternary(decimal)
        ternValue = ternValue.zfill(20)     # Make sure strings are exactly 20 characters
        return ternValue

    def ternary (self, n):
        if n == 0:
            return '0'
        nums = []
        while n:
            n, r = divmod(n, 3)
            nums.append(str(r))
        return ''.join(reversed(nums))

    def extractTxFrame(self, f1, f2):
        bits = f1 + f2
        fixed = ""
        rolling = ""

        for i in range (0, len(bits)):
            if i % 2 == 0:
                fixed += bits[i]
            else:
                rolling += bits[i]
        return fixed, rolling

    def generateTxFrame(self, frame1, frame2):
        f1 = self.hex2tern(frame1)
        f2 = self.hex2tern(frame2)
        bits = ""
        assert(len(f1) == len(f2))
        for i in range (0, len(f1)):
            bits += f1[i]
            bits += f2[i]
        return bits

    def parseUnoPacket(self, packet):
        packet = packet.decode("utf-8")
        packet = packet[:-1]    # Remove trailing \r

        op = 'hex'
        frames = packet.split()

        fixed, rolling = self.extractTxFrame(frames[0], frames[1])

        #if reverse_roll:
        #    rolling = rolling[::-1]

        fixed = self.tern2bin(fixed, op)
        rolling = self.tern2bin(rolling, op)

        #print "TX ", fixed[0], fixed[1:4], fixed[4:8], rolling
        print "TX ", fixed, rolling, "\tRaw ", packet

        #print "TX", self.tern2bin(frames[0], 'hex'), self.tern2bin(frames[1], 'hex')

    def parseSam3UPacket(self, packet):
        packet = packet.decode("utf-8")
        packet = packet[:-1]    # Remove trailing \r

        if len(packet) not in (9, 25):
            print ("RX Err: Invalid packet, length must be 9 or 25 bits")
            return
        elif packet[0] != '1':
            print ("RX Err: Invalid start bit")
            return
        opcode = packet[1:3]
        if opcode == '10' or opcode == '01':
            address = packet[3:9]
            data = packet[9:25]
            if opcode == '10':
                command = 'R'
            elif opcode == '01':
                data = data[::-1]           # Reverse data since it's LSB first
                command = 'W'

            address = int(address, 2)
            data = int(data, 2)
            print ("RX %c %02x %04x %s") % (command, address, data, packet)

    def exit(self):

        time.sleep(0.1)
        # Shutdown serial module
        if self.uno_port != None:
            self.uno_serial.close()
        if self.sam3u_port != None:
            self.sam3u_serial.close()

    def run(self):
        while True:
            c = raw_input()
            if c == 't':
                self.sendChar(self.uno_serial, 't')
            elif c == 'f':
                print("Enter 32 byte packet to transmit. e.g \"76c94d67 37f95796\"")
                packet = raw_input()
                frame = packet.split()
                bitstream = self.generateTxFrame(frame[0], frame[1])
                self.sendChar(self.uno_serial, 'f')
                self.sendString(self.uno_serial, bitstream)
            elif c == 'h':
                print ("t - transmit next valid packet")
                print ("f - transmit next fake packet")
                print ("h - help")
            else:
                print ("Unrecognized command, try \"h\" to see list of commands")


if __name__ == '__main__':
    sniffer = GdSniffer()
    try:
        print("")
        sniffer.run()
    except KeyboardInterrupt:
        sniffer.exit()



