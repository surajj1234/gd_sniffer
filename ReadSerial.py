import serial
import threading
from Queue import Queue
import os
import time
from copy import deepcopy

BAUDRATE = 115200
TIMEOUT = 0
'''
timeout = None: wait forever / until requested number of bytes are received
timeout = 0: non-blocking mode, return immediately in any case,
            returning zero or more, up to the requested number of bytes
timeout = x: set timeout to x seconds (float allowed) returns immediately when
        	the requested number of bytes are available, otherwise wait until the
            timeout expires and return all bytes that were received until then.
'''

PRINT_RX_AND_TX_VALUES = 0
PRINT_RX_VALUE = 1
PRINT_TX_VALUE = 2
PRINT_RX_PACKET_VALUE = 3

RX_START_BYTE = '#'
RX_END_CARRIAGE_RETURN = '\n'

PACKET_SOF = 0
PACKET_DATA = 2

DEBUG_STATE = 2


class ReadSerial():


	def __init__(self,comport,ph):

		self.rxQueue = Queue()
		self.terminate = False
		self.baudRate = BAUDRATE

		self.comms = serial.Serial(comport, self.baudRate, timeout = TIMEOUT, rtscts = 0)

		self.rxPacket = bytearray()
		self.txPacket = bytearray()
		self.rxState = PACKET_SOF
		self.rxPacket2 = bytearray()

		self.packetHandler = ph

		self.start_threads()



	def start_threads(self):

		self.thread_list = []

		'''
		Starting rx thread and state machine thread
		'''
		self.thread_list.append(threading.Thread(target = self.com_rx_thread))
		self.thread_list.append(threading.Thread(target = self.com_state_machine))

		#daemon threads are killed when the program shuts down
		for thread in self.thread_list:
			thread.daemon = True

		for thread in self.thread_list:
			thread.start()



	def close(self):

		self.terminate = True
		time.sleep(1)
		self.comms.close()


	def writeSerial(self, writePacket):

		self.comms.write(writePacket)


	def com_rx_thread(self):

		while self.terminate == False:

			byteChar = self.comms.read(1) #number of bytes to read

			if (byteChar != b''):
				self.rxQueue.put(byteChar)

	def finalPacket(self):
		return self.rxPacket2


	def com_state_machine(self):

		while self.terminate == False:

			#get the latest byte from the queue
			#is this actually the latest
			rxByte = self.rxQueue.get()[0]


			if (DEBUG_STATE == 1 or DEBUG_STATE == PRINT_RX_AND_TX_VALUES):
				print((rxByte))


			if (self.rxState == PACKET_SOF):
				#print("Starting frame")

				if (rxByte == RX_START_BYTE):
				    #self.rxState = PACKET_LEN
				    #we are skipping the part where we get length in the 2nd byte
				    self.rxState = PACKET_DATA

			elif self.rxState == PACKET_DATA:
				if (rxByte == RX_END_CARRIAGE_RETURN):
					self.rxState = PACKET_SOF

					if DEBUG_STATE == 3:

						hexstring = ":".join("%02x" % x for x in self.rxPacket)
						print("RX  " + hexstring)

					self.rxPacket2 = deepcopy(self.rxPacket)
					self.packetHandler(self.rxPacket2)
                                        del self.rxPacket[:]
				else:
					self.rxPacket.append(rxByte)


