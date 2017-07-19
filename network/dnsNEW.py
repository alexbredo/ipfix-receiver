#-*- coding: utf-8 -*-

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

from itertools import chain
from dns import resolver, reversename

class DNS:
	def __lookupCNAME(self, hostname):
		try:
			answers = resolver.query(hostname, 'CNAME')
			return list(chain.from_iterable([self.__lookupA(str(cname)) for cname in answers]))
			# TODO: Evtl. müssen alle weitern CNAME-Einträge in der Kette geprüft werden... bis ein A-Record existiert
		except (resolver.NoAnswer, resolver.NXDOMAIN):
			return []
		
	def __lookupA(self, hostname):
		try:
			answers = resolver.query(hostname, 'A')
			return [str(ip) for ip in answers]
		except (resolver.NXDOMAIN, resolver.NoAnswer):
			return []
		
	def getName(self, ip):
		try:
			return str(resolver.query(reversename.from_address(ip), "PTR")[0])[:-1] # Remove Last '.'
		except resolver.NXDOMAIN:
			return 'error.unknown.domain'
			
	def getIPs(self, hostname):
		a = self.__lookupA(hostname)
		if a:
			return a
		else:
			return self.__lookupCNAME(hostname)

			
import time
import random
from network.dns import DNS
from base.database import DatabaseTable

# Persistent DNS-Cache
class DNSCached:
	def __init__(self, ttl=3600):
		self.dns = DNS()
		self.db = DatabaseTable([('ip', 'text'), ('hostname', 'text'), ('timestamp', 'int')], 'dns', 'cache')
		self.ttl = ttl
		
	def __isTTLValid(self, timestamp):
		# Mit zufälliger TTL-Ergänzung um Abfragen nach einer festen Zeitspanne zu vermeiden (Coldstart)
		return (time.time() - timestamp) <= (self.ttl + random.randint(0, self.ttl / 4))
		
	def getName(self, ip):
		condition = 'ip = "%s"' % ip
		r = self.db.select(['hostname', 'timestamp'], condition)
		if r: # cache-hit
			hostname, timestamp = r[0]
			if self.__isTTLValid(timestamp): # new entry
				return hostname
			else: # old entry
				self.db.delete('ip = "%s"' % ip) # Flush old data
				return self.__getAndCacheHostname(ip)
		else: # cache-miss
			return self.__getAndCacheHostname(ip)
			
	def __getAndCacheHostname(self, ip):
		hostname = self.dns.getName(ip)
		self.db.insert({'ip': ip, 'hostname': hostname, 'timestamp': int(time.time())})
		self.db.commit()
		return hostname
			
	def getIPs(self, hostname):
		condition = 'hostname = "%s"' % hostname
		r = self.db.select(['ip', 'timestamp'], condition)
		if r: # cache-hit
			if self.__isTTLValid(r[0][1]): # Check timestamp of first entry
				return [h[0] for h in r]
			else:
				self.db.delete('hostname = "%s"' % hostname) # Flush old data
				return self.__getAndCacheIPs(hostname)
		else: # cache-miss
			return self.__getAndCacheIPs(hostname)
		
	def __getAndCacheIPs(self, hostname):
		ips = self.dns.getIPs(hostname)
		for ip in ips:
			self.db.insert({'ip': ip, 'hostname': hostname, 'timestamp': int(time.time())})
		self.db.commit()
		return ips

'''
d = DNSCached()
print(d.getName('8.8.8.8'))
print(d.getIPs('www.microsoft.de'))
'''