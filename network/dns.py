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

import socket, time, pickle, os
from random import randint
#from multiprocessing import Pool
#from multiprocessing.context import TimeoutError
'''
TODO: 
 - DNS-Cache Cleanup Funktion (?) für veraltete Einträge
 - Nice-to-have: 
'''

class DNSCache():
	SAVE_FILE = "dns-cache.data"
	SAVE_INTERVAL = 100000
	
	def __init__(self, ttl=10800):
		self.interval = 0
		self.ttl = ttl
		self.data = dict() # ip -> (name, zeitstempel)
		#self.resolver_pool = Pool(processes=workers)
		try:
			if os.path.isfile(DNSCache.SAVE_FILE):
				self.data = pickle.load(open(DNSCache.SAVE_FILE, "rb"))
		except:
			print("Could not load DNS-Cache-File: %s." % DNSCache.SAVE_FILE)
			
	def store(self):
		print("DNS-Cache-Maintenance: Cleanup-and-Store-Task running.")
		self.cleanup()
		pickle.dump(self.data, open(DNSCache.SAVE_FILE, "wb"))
		
	def cleanup(self):
		for k,v in sorted(self.data.items()):
			if time.time() - v[1] > self.ttl:
				del(self.data[k])

	def do_jobs(self):
		self.interval += 1

		if self.interval >= DNSCache.SAVE_INTERVAL:
			# Regularly store results
			self.store()
			# Reset Counter (Prevent huge counters)
			self.interval = 0
			
	def getName(self, ip):
		self.do_jobs()
		
		if ip in self.data:
			name = self.data[ip][0]
			timestamp = self.data[ip][1]
			if (timestamp < time.time() - (self.ttl + randint(0, 3600))): # Zufällige TTL-Ergänzung um Abfragen nach einer festen  Zeitspanne zu vermeiden (Coldstart)
				self.data[ip] = (self.getNameFromNameserver(ip), time.time()) # cache miss. new request.
			return self.data[ip][0]
		else:
			self.data[ip] = (self.getNameFromNameserver(ip), time.time()) 
			return self.data[ip][0]
			
	def getNameFromNameserver(self, ip):
		self.do_jobs()
		
		try:
			result = socket.gethostbyaddr(ip) # (hostname, alias-list, IP)
			return result[0]
		except (socket.gaierror, socket.error): # (TimeoutError, socket.gaierror):
			return ip
			
	'''
	def getNameFromNameserver(self, ip, timeout=1):
		try:
			self.resolver_pool = Pool(processes=self.workers) # Das funktioniert iwi (noch?) nicht pro Klasse (?)
			d = self.resolver_pool.apply_async(socket.gethostbyaddr, (ip,))
			result = d.get(timeout=timeout) # (hostname, alias-list, IP)
			return result[0]
		except: # (TimeoutError, socket.gaierror):
			return ip
	'''	
	
	def cachesize(self):
		return len(self.data.keys())
		
'''
if __name__ == '__main__':
	d = DNSCache()
	print(d.getName('sfdsfdfg.de'))
	print(d.getName('dsgfsahghf.de'))
	print(d.getName('130.10.224.8'))
	print(d.getName('99.99.99.99'))
'''