#!/usr/bin/python3
# -*- coding: utf-8 -*-

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

import socket
import sys
import pickle

class UDPSender():
	def __init__(self, host, port, mtu=9000):
		self.host, self.port = host, port
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.__mtu = mtu
		self.__chunksize = 9#int(9000 / 2000) # approximation to fit into mtu initially
		
	def send(self, mylist):
		for chunk in self.chunks(mylist, 5):
			data = pickle.dumps(chunk)
			newchunksizerecommendation = int((self.__mtu / len(data)) - 1)
			if self.__chunksize > newchunksizerecommendation:
				self.__chunksize = newchunksizerecommendation
				print("Chunksize decreased to %s to fit into MTU." % self.__chunksize)
			self.sock.sendto(data, (self.host, self.port))
		
	def chunks(self, l, n):
		for i in iter(range(0, len(l), n)):
			yield l[i:i+n]
		
if __name__ == "__main__":
	us = UDPSender("127.0.0.1", 9999)
	us.send({'a': 1})
