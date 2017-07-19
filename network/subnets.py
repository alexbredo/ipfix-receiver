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

import ipaddress # for subnetchecking
from base.appconfig import Configuration
from base.applog import *

class HomeNetworkChecker():
	# zwecks Bestimmung der Richtung des Flows (oder später ggf. autonom einlernen?)
	
	def __init__(self):
		config = Configuration()
		self.networks = config.exporter_networks
		self.error_written_exporter = dict()
		#self.error_written_networks = dict() # das macht keinen sinn, da nicht alle netze definiert werden können (inet) --> log trash
	
	def isThisIPinItsHomeNetwork(self, exporter, ip, exportInterface = None):
		try:
			if exportInterface:
				exporter = "%s:%s" % (exporter, exportInterface)
			for net in self.networks[exporter]['networks']:
				#print (exporter, net, ip)
				if ipaddress.ip_address(ip) in ipaddress.ip_network(net, strict=False):
					return self.networks[exporter]
				#if ip not in self.error_written_networks:
				#	log.warning("Exporter '%s' defined, but it does not include IP %s (add network in config)." % (exporter, ip))
				#	self.error_written_networks[ip] = True
			else:
				return False
		except KeyError:
			if exporter not in self.error_written_exporter:
				log.warning("Exporter '%s' and its networks not defined in config." % exporter)
				self.error_written_exporter[exporter] = True
		except Exception as e:
			log.error(e) # Invalid IP
		return False
		

from network.iprange import IPRangeLookupManager
class LocationClassifier():
	def __init__(self):
		self.iprlm = IPRangeLookupManager()
		for item in Configuration().networks:
			for net in item[1]: 				# 1: NetworkS
				self.iprlm.addSubnet(net, item[0]) 	# 0: City
		self.iprlm.prepare()

	def getLocation(self, myip):
		return self.iprlm.lookupIP(myip)