# Copyright (c) 2014 Alexander Bredo
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or 
# without modification, are permitted provided that the 
# following conditions are met:
# 
# 1. Redistributions of source code must retain the above 
# copyright notice, this list of conditions and the following 
# disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above 
# copyright notice, this list of conditions and the following 
# disclaimer in the documentation and/or other materials 
# provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND 
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF 
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE 
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR 
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF 
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT 
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.

import socket, struct
from socket import inet_ntoa
import atexit	
import math
import ipaddress

class ExceptionInvalidNetflowVersion(Exception):
    pass
class ExceptionInvalidNetflowHeader(Exception):
    pass
class ExceptionNoCallbackMethod(Exception):
    pass
	
class NetflowV5: # Observable
	SIZE_OF_HEADER = 24
	SIZE_OF_RECORD = 48

	def __init__(self, netflow_ip_mask = '0.0.0.0', netflow_port = 2055):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind((netflow_ip_mask, netflow_port))
		atexit.register(self.exit_handler)
		self.enabled = True
		
	def subscribe(self, callback_method):
		if not callback_method:
			raise ExceptionNoCallbackMethod('A call back method must be spcified!')
			
		while self.enabled:
			header = {}
			
			buf, addr = self.sock.recvfrom(1500)
			header['exporter'] = addr[0]
			header['exportInterface'] = None
	
			# Unpack the header
			header_raw = struct.unpack('!HHIIIIBBH', buf[:NetflowV5.SIZE_OF_HEADER])
			
			# Sanity check - fields
			if len(header_raw) != 9:
				raise ExceptionInvalidNetflowHeader("Netflow v5 must contain exactly 9 elements.")
				
			
			header['version'] = header_raw[0] 		# version = 5
			
			header['flow_count'] = header_raw[1] 	# The number of records in the PDU
			header['sys_uptime'] = header_raw[2] 	# Current time in millisecs since router booted (not in IPFIX!)
			if header_raw[4] == 0: # Residual nanoseconds since 0000 UTC 1970 
				header['timestamp'] = header_raw[3]	# Current seconds since 0000 UTC 1970
			else:
				header['timestamp'] = header_raw[3] + (header_raw[4] / 1000000000)
			header['sequence'] = header_raw[5]		# Seq counter of total flows seen
			header['engine_type'] = header_raw[6]	# Type of flow switching engine (RP,VIP,etc.)
													# Engine 0 - Regular netflow
													# Engine 1 - Regular netflow
													# Engine 2 - Only sampled netflow
													# Engine 3 - Both, sample and aggregate netflow
													# Engine 4 and 4+ - Only sampled netflow
			header['domain_id'] = header_raw[7]		# Slot number of the flow switching engine
			header['sampling_interval'] = header_raw[8]	# reserved / not used?

			# Sanity check - version
			if header['version'] != 5:
				raise ExceptionInvalidNetflowVersion("Not a NetFlow v5 packet.")

			# Sanity check - count
			if header['flow_count'] <= 0:
				raise ExceptionInvalidNetflowHeader("Invalid header count {0}".format(header['flow_count']))

			for i in range(0, header['flow_count']):
				base = NetflowV5.SIZE_OF_HEADER+(i*NetflowV5.SIZE_OF_RECORD)

				data = struct.unpack('!HHIIIIHHBBBBHHBBH',buf[base+12:base+NetflowV5.SIZE_OF_RECORD])

				nfdata = {}

				# Decode the addresses
				nfdata['sourceIPv4Address'] = ipaddress.ip_address(inet_ntoa(buf[base+0:base+4]))	# Source IP Address
				nfdata['destinationIPv4Address'] = ipaddress.ip_address(inet_ntoa(buf[base+4:base+8]))	# Destination IP Address
				nfdata['ipNextHopIPv4Address'] = ipaddress.ip_address(inet_ntoa(buf[base+8:base+12]))	# Next hop router's IP Address

				# The rest of the data
				nfdata['ingressInterface'] = data[0]			# Input interface index 
				nfdata['egressInterface'] = data[1]				# Output interface index
				nfdata['packetDeltaCount'] = data[2]			# Packets sent in Duration 
				nfdata['octetDeltaCount'] = data[3]				# Octets sent in Duration
				nfdata['flowStartSysUpTime'] = data[4]			# SysUptime at start of flow
				nfdata['flowEndSysUpTime'] = data[5]			# and of last packet of flow
				nfdata['sourceTransportPort'] = data[6]			# TCP/UDP source port number or equivalent
				nfdata['destinationTransportPort'] = data[7]	# TCP/UDP destination port number or equiv
				# nfdata['pad1'] = data[8] 						# unused
				nfdata['tcpControlBits'] = data[9] 				# Cumulative OR of tcp flags
				
				# https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers
				nfdata['protocolIdentifier'] = data[10] 		# IP protocol, e.g., 6=TCP, 17=UDP, ...
				
				nfdata['ipClassOfService'] = data[11]			# IP Type-of-Service
				nfdata['bgpSourceAsNumber'] = data[12]			# originating AS of source address
				nfdata['bgpDestinationAsNumber'] = data[13]		# originating AS of destination address
				nfdata['sourceIPv4PrefixLength'] = data[14]		# source address prefix mask bits
				nfdata['destinationIPv4PrefixLength'] = data[15]# destination address prefix mask bits
				#nfdata['pad2'] = data[16] 						# unused, drops
				
				# Python 3.5 only (fast merge via pointer):
				flow = {**header, **nfdata}
				callback_method (flow)
				
	def exit_handler(self):
		self.enabled = False
		print("Exit handler") # Print summary or status


class FlowReceiver:
	def __init__(self):
		o = NetflowV5()
		try:
			o.subscribe(self.insertFlow)
		except KeyboardInterrupt:
			print("Exit. Bye bye.")
		
	def insertFlow(self, flow):
		print(flow)
		
## Test:
# FlowReceiver()
