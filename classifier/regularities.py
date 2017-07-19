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

import time
import os
import pickle

class KnownPartners:
	SAVE_FILE = "sec.partners.data"
	SAVE_INTERVAL = 100000
	
	def __init__(self): 
		self.interval = 0
		self.data = dict()
		if os.path.isfile(KnownPartners.SAVE_FILE):
			self.data = pickle.load(open(KnownPartners.SAVE_FILE, "rb"))
			
	def store(self):
		print("KnownPartners-Maintenance: Cleanup-and-Store-Task running.")
		self.cleanup()
		pickle.dump(self.data, open(KnownPartners.SAVE_FILE, "wb"))

	def do_jobs(self):
		self.interval += 1

		if self.interval >= KnownPartners.SAVE_INTERVAL:
			# Regularly store results
			self.store()
			# Reset Counter (Prevent huge counters)
			self.interval = 0
			
	def getRisk(self, src, dst):
		self.do_jobs()
		
		conv_id = self.__order(src, dst)
		if conv_id in self.data: # update count, last_seen
			self.data[conv_id]['last_seen'] = time.time()
			if self.data[conv_id]['count'] < 1000: # Nur bis 1000 zählen - Rest äquivalent
				self.data[conv_id]['count'] += 1
		else:
			self.data[conv_id] = {
				'first_seen': time.time(),
				'last_seen': time.time(),
				'count': 1, 
			}
		return self.__checkAll(conv_id)
		
	def __order(self, a, b):
		if a < b:
			return "%s-%s" % (a,b)
		else:
			return "%s-%s" % (b,a)

	def __checkAll(self, id):
		cd = self.__checkDuration(self.data[id]['first_seen'], self.data[id]['last_seen'], id)
		cc = self.__checkCount(self.data[id]['count'], id)
		return ((cd[0] + cc[0]) / 2, "%s %s" % (cd[1],cc[1]))
		
	def __checkCount(self, count, id):
		if count <= 10: 		# Ausnahmezugriffe
			return (-0.5, '%s have less than 10 conversations.' % id)
		elif count <= 100: 		# gehäufte Zugriffe
			return (0.25, '%s have less than 100 conversations.' % id)
		elif count <= 500: 		# häufige Zugriffe
			return (0.75, '%s have less than 500 conversations.' % id)
		else: 				# reguläre Zugriffe
			return (1, '%s have regular conversations.' % id)
			
	def __checkDuration(self, first, last, id):
		d = last - first
		if d <= 3600: 		# 1 Stunde; Ausnahmezugriffe
			return (-0.5, 'Conversation between %s known for less than one hour.' % id)
		elif d <= 86400: 	# 1 Tag; gehäufte Zugriffe
			return (0.25, 'Conversation between %s known for less than one day.' % id)
		elif d <= 604800: 	# 1 Woche; häufige Zugriffe
			return (0.75, 'Conversation between %s known for less than one week.' % id)
		else: 				# reguläre Zugriffe
			return (1, 'Conversation between %s known for %s days.' % (id, d/86400))
			
	def cleanup(self):
		# Delete items not seen since 2 Weeks. Probably ressource intensive ...
		for k,v in sorted(self.data.items()):
			if time.time() - v['last_seen'] > 1209600:
				print('Cleanup %s.' % k)
				del(self.data[k])

# Idea: one of partners known ... with count - probability, first_seen, last_seen
class KnownHost:
	SAVE_FILE = "sec.hosts.data"
	SAVE_INTERVAL = 100000
	
	def __init__(self):
		self.interval = 0
		self.data = dict()
		if os.path.isfile(KnownHost.SAVE_FILE):
			self.data = pickle.load(open(KnownHost.SAVE_FILE, "rb"))
		
	def store(self):
		print("KnownHost-Maintenance: Cleanup-and-Store-Task running.")
		self.cleanup()
		pickle.dump(self.data, open(KnownHost.SAVE_FILE, "wb"))
		
	def do_jobs(self):
		self.interval += 1

		if self.interval >= KnownHost.SAVE_INTERVAL:
			# Regularly store results
			self.store()
			# Reset Counter (Prevent huge counters)
			self.interval = 0
			
	# Bewertungskriterien: (a) schon mal gesehen (b) wie viel (c) wie lange ...
	def getRisk(self, ip):
		self.do_jobs()
		
		if ip in self.data:
			# update count, last_seen
			self.data[ip]['last_seen'] = time.time()
			if self.data[ip]['count'] < 1000: # Nur bis 1000 zählen - Rest äquivalent
				self.data[ip]['count'] += 1
			#return self.data[ip]
		else:
			self.data[ip] = {
				'first_seen': time.time(),
				'last_seen': time.time(),
				'count': 1, 
			}
		return self.__checkAll(ip)

	def __checkAll(self, ip):
		cd = self.__checkDuration(self.data[ip]['first_seen'], self.data[ip]['last_seen'], ip)
		cc = self.__checkCount(self.data[ip]['count'], ip)
		return ((cd[0] + cc[0]) / 2, "%s %s" % (cd[1],cc[1]))
		
	def __checkCount(self, count, ip):
		if count <= 10: 		# Ausnahmezugriffe
			return (-0.5, 'Host %s has less than 10 Conversations.' % ip)
		elif count <= 100: 		# gehäufte Zugriffe
			return (0.25, 'Host %s has less than 100 Conversations.' % ip)
		elif count <= 500: 		# häufige Zugriffe
			return (0.75, 'Host %s has less than 500 Conversations.' % ip)
		else: 				# reguläre Zugriffe
			return (1, 'Regular conversations by Host %s.' % ip)
			
	def __checkDuration(self, first, last, ip):
		d = last - first
		if d <= 3600: 		# 1 Stunde; Ausnahmezugriffe
			return (-0.5, 'Host %s known for less than one hour.' % ip)
		elif d <= 86400: 	# 1 Tag; gehäufte Zugriffe
			return (0.25, 'Host %s known for less than one day.' % ip)
		elif d <= 604800: 	# 1 Woche; häufige Zugriffe
			return (0.75, 'Host %s known for less than one week.' % ip)
		else: 				# reguläre Zugriffe
			return (1, 'Host %s known for %s days.' % (ip, d/86400))
			
	def cleanup(self):
		# Delete items not seen since 2 Weeks. Probably ressource intensive ...
		for k,v in sorted(self.data.items()):
			if time.time() - v['last_seen'] > 1209600:
				print('Cleanup %s.' % k)
				del(self.data[k])

#kp = KnownPartners()
#for x in range(0,3000):
#print(kp.getRisk('127.0.0.1', '127.0.0.2'))