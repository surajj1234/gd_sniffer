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
            self.sendChar(serial, 's')
            time.sleep(0.2)
            if self.statusPacket == "UNO\r":
                self.uno_port = i
            elif self.statusPacket == "SAM3U\r":
                self.sam3u_port = i
            serial.close()

        #self.serial = ReadSerial.ReadSerial(base_comport, self.parsePacket)

    def sendChar(self, serial, a):
        txstring = a
        txPacket = bytearray()
        txPacket.extend(map(ord, txstring))
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

    def exit(self):

        time.sleep(0.1)
        # Shutdown serial module
        #self.serial.close()

    def run(self):
        #while True:
        pass


if __name__ == '__main__':
    sniffer = GdSniffer()
    try:
        sniffer.run()
    except KeyboardInterrupt:
        sniffer.exit()



