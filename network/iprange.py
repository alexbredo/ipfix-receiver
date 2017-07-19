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

from bisect import bisect_left
import ipaddress

class IPRangeLookupManager():
	def __init__(self):
		self.data = []
		self.__changed = True
		
	def addSubnet(self, subnet, attribute):
		net = ipaddress.ip_network(subnet, strict=False)
		return self.addIPByNum(int(net[0]), int(net[-1]), attribute)
	
	def addIP(self, start_ip, end_ip, attribute):
		self.addIPByNum(int(ipaddress.ip_address(start_ip)), int(ipaddress.ip_address(end_ip)), attribute)
		
	def addIPByNum(self, start_ip, end_ip, attribute):
		self.data.append((start_ip, end_ip, attribute))
		self.__changed = True
		
	def prepare(self):
		self.data.sort(key=lambda r: r[0])
		self.keys = [y for _,y,_ in self.data]
		self.__changed = False
		#print("[IPRangeLookupManager] IP-Ranges were (re)loaded.")
		
	def lookupIP(self, ip):
		return self.lookupIPbyNum(int(ipaddress.ip_address(ip)))
			
	def lookupIPbyNum(self, ipnum):
		if self.__changed:
			self.prepare()
		try:
			result = self.data[bisect_left(self.keys, ipnum)]
			if ipnum >= result[0] and ipnum <= result[1]:
				return result[2]
			return None
		except IndexError:
			return None
			
if __name__ == '__main__':
	ipm = IPRangeLookupManager()
	
	for x in range(1, 4294967295, 16000):
		ipm.addIPByNum(x, x + 8000, 'Trojan-Site: %s' % x)
	
	print(ipm.lookupIPbyNum(3275152001))
	print(ipm.lookupIPbyNum(3275161001))
	print(ipm.lookupIPbyNum(3275169003))