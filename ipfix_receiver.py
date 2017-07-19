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


import socketserver
from ipfix.workers import Manager
from base.applog import *
from netflow.netflow_v5 import NetflowV5

class ExceptionInvalidNetflowVersion(Exception):
	pass
	
class IPFIXUDPHandler(socketserver.DatagramRequestHandler):
	def handle(self):
		log.debug('IPFIX-Message received from %s' % self.client_address[0])
		self.server.ipfix_manager.put((self.request[0], str(self.client_address[0])))
		
class NetflowV5Handler():
	def __init__(self, manager):
		self.manager = manager
		
	def handle(self, flow):
		log.debug('Netflow-Message received.')
		self.manager.putNetflow(flow)
		
if __name__ == "__main__":
	mgr = Manager()
	if mgr.config.netflow_version == 10:
		server = socketserver.UDPServer((
			mgr.config.netflow_ip_mask, 
			mgr.config.netflow_port
		), IPFIXUDPHandler)
		server.ipfix_manager = mgr
		log.info("Listening on %s:%s" % (
			mgr.config.netflow_ip_mask, 
			mgr.config.netflow_port
		))
		log.info("Waiting for First IPFIX Template.")
		try:
			mgr.start()
			#server.ipfix_manager.start()
			server.serve_forever()
		except KeyboardInterrupt:
			log.info("Graceful Exit")
			server.ipfix_manager.join()
	elif mgr.config.netflow_version == 5:
		o = NetflowV5(mgr.config.netflow_ip_mask, mgr.config.netflow_port)
		n = NetflowV5Handler(mgr)
		try:
			mgr.start()
			o.subscribe(n.handle) 	# register Callback method
		except KeyboardInterrupt:
			print("Exit. Bye bye.")
	else:
		raise ExceptionInvalidNetflowVersion('Only Netflow v5 or IPFIX (=Netflow v10) are supported.')
