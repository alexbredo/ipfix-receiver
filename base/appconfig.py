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

# Idee Config + Argumente in einem definieren
# die Argumente, die erwartet werden, auch in der Config suchen.
# + Sample Config Generator
# Prio: Argumente vor Config

import argparse, sys, logging
from base.xmlserializer import Serializable
from base.applog import *

# Singleton Pattern. Get same instance via "c = Configuration()" every time again
class Configuration(Serializable):
	_instance = None
	
	def __new__(cls, *args, **kwargs):
		if not cls._instance:
			cls._instance = super(Configuration, cls).__new__(cls, *args, **kwargs)
			cls._instance.__setup()
		return cls._instance
		
	def __setup(self, *args, **kwargs):
		# Private:
		self.__version = '0.6'
		self.__appname = 'ipfix_receiver'
		# Defaults:
		self.netflow_version = 10
		self.netflow_port = 4739
		self.netflow_ip_mask = '0.0.0.0'
		self.flow_log_interval = 10
		self.ipfix_extreme_network_patch = False
		self.ipfix_cache_seconds = 30
		self.queues_maxsize = 80000
		self.dns_cache_seconds = 21600
		self.conversation_consumer_threads = 2
		self.corrector_consumer_threads = 2
		self.enabled_handlers = {
			'elasticsearch': False, 
			'screen': False,
			'file': True,
			'udpreceiver': False
		}
		self.elasticsearch = {
			'host': '127.0.0.1', 
			'port': 9200, 
			'index': 'ipfix'
		}
		self.udpreceiver = {
			'host': '127.0.0.1', 
			'port': 9999
		}
		self.filename = 'ipfix.conversations.txt'
		self.exporter_networks = {
			'192.168.1.107:1002': { 'networks': ['150.10.0.0/16'], 'label': 'Washington' },
			'127.0.0.1': { 'networks': ['127.0.0.0/24'], 'label': 'Local' }
		} 
		self.networks = [
			('Washington', ['150.10.0.0/16']),
			('Localhost', ['127.0.0.0/24']),
			('Localnet', ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']),
		]
		self.opensocketcache = {
			'ttl_response_received': 60,
			'ttl_no_response': 600
		} 
		self.security_sample_percentage = 0.1

		# Config File:
		super().__init__('config.xml')
		self.__parseArguments()
		self.__handleArguments()
		
	def __parseArguments(self):
		ap = argparse.ArgumentParser(description="Dump IPFIX-Messages collected over UDP")
		ap.add_argument('-v', '--version', help='Print Version', action='store_true')
		ap.add_argument('-c', '--config', metavar='Configfile', help='Which config-file to use (default: config.xml)')
		ap.add_argument('-d', '--defaultconfig', metavar='Configfile', help='Write sample Config with default values')
		self.__args = ap.parse_args()
		
	def __handleArguments(self):
		if self.__args.version:
			print("%s. Version: %s" % (self.__appname, self.__version))
			print("(c) 2014 by Alexander Bredo, EDAG AG")
			sys.exit(0)
		if self.__args.defaultconfig:
			self._filename = self.__args.defaultconfig
			self.save()
			print("Default config has been generated. See %s" % self._filename)
			sys.exit(0)
		if self.__args.config:
			self._filename = self.__args.config
		try:
			self.load()
			log.info("Using %s as configuration." % self._filename)
		except FileNotFoundError:
			log.info("Configuration file '%s' was not found. Using default values." % self._filename)

			
#Configuration()