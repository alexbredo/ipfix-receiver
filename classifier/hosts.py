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

import re
import hashlib
import urllib3
import os
import math
import ipaddress
import time

from urllib.parse import urlparse
from lex.parser import SyntaxParser
from network.iprange import IPRangeLookupManager

class BlacklistReader:
	DIRECTORY = 'download_cache'
	CACHE_TTL = 86400 # One Day
	
	def __init__(self, feedUrl, reason, lineStartsNotWith, listtype):
		self.feedUrl = feedUrl
		self.lineStartsNotWith = lineStartsNotWith
		self.listtype = listtype # White oder Blacklist
		self.reason = reason
		self.irlm = IPRangeLookupManager()
		self.__load()
		self.__parse()
	
	def __getFilename(self):
		if self.feedUrl in ['whitelist', 'blacklist']:
			return os.path.join(BlacklistReader.DIRECTORY, self.feedUrl)
		else:
			return os.path.join(BlacklistReader.DIRECTORY, hashlib.sha224(self.feedUrl.encode('utf-8')).hexdigest())
		
	def __load(self):
		if self.feedUrl in ['whitelist', 'blacklist']: return # Offline files ...
		
		filename = self.__getFilename()
		if not os.path.isfile(filename):
			# Download
			self.__download(filename)
		else:
			if (time.time() - os.path.getmtime(filename) > BlacklistReader.CACHE_TTL):
				# Download
				self.__download(filename)
			else:
				print("Loading '%s' from Cache" % self.feedUrl)
		# Cache
			
	def __download(self, filename):
		try:
			print("Downloading '%s'" % self.feedUrl)
			http = urllib3.PoolManager()
			r = http.request('GET', self.feedUrl)
			
			if math.floor(r.status / 100) != 2:
				print("Error while loading %s. (HTTP-Status: %i)" % (self.feedUrl, r.status))
				return 
				
			fo = open(filename, "wb")
			fo.write(r.data)
			fo.close()
		except urllib3.exceptions.ProtocolError as e:
			print(e, self.feedUrl)
	
	def getRisk(self, ip):
		return self.irlm.lookupIP(ip)
	
	def __parse(self):
		try:
			sp = SyntaxParser()
			fo = open(self.__getFilename(), 'r')
			for line in fo:
				line = line.strip()
				if not line: continue
				if line.startswith(self.lineStartsNotWith): continue
				
				uni = self.getUnified(sp.getTokens(line))
				if uni:
					for s,e in uni:
						self.irlm.addIP(s, e, (self.listtype, self.reason))
			fo.close()
		except FileNotFoundError:
			print("Error in Securitymodule. File does not exist. Probably not downloaded properly: %s" % self.feedUrl)

	def getUnified(self,tokens):
		#dns_cache = DNSCache()
		bucket = { 'IPV4': [], 'NET_CIDR': [], 'DOMAIN': [], 'URL': [] }
		for type,value in tokens:
			try:
				bucket[type].append(value)
			except KeyError: pass
		for type,items in bucket.items():
			try:
				if items:
					if type == 'NET_CIDR':
						networks = [ipaddress.ip_network(net) for net in items]
						return [(net[0], net[-1]) for net in networks]
					elif type == 'IPV4':
						if len(items) == 1: # Single IP
							the_ip = self.__fixIP(items[0])
							return [(the_ip, the_ip)]
						elif len(items) == 2: # IP Range
							return [tuple(self.__fixIP(ip) for ip in items)]
					elif type == 'DOMAIN':
						#return [dns_cache.getIP(domain) for domain in items] # Flatten? Multiple IP...
						pass
					elif type == 'URL':
						#return [dns_cache.getIP(urlparse(url).netloc) for url in items] # Flatten? Multiple IP...
						pass
			except ValueError as e:
				print ('[ignore]', e)
					
	def __fixIP(self, ip_str):
		# Remove trailing zeros: 061.074.001.223 --> 61.74.1.223
		ip_str = re.sub("(^00|^0)(?=\d)", "", ip_str)
		ip_str = re.sub("(\.00|\.0)(?=\d)", ".", ip_str)
		return ipaddress.ip_address(ip_str)
		
class ListType:
	WHITELIST = 10 # Gewichtung der anderen überdecken
	BLACKLIST = -1
	
blacklists = [
	('whitelist', 'CUSTOM WHITELIST', '#', ListType.WHITELIST),
	('blacklist', 'CUSTOM BLACKLIST', '#', ListType.BLACKLIST),
	('http://atlas-public.ec2.arbor.net/public/ssh_attackers', 'ARBOR ATLAS SSH Attacker', '#', ListType.BLACKLIST),
	('http://charles.the-haleys.org/ssh_dico_attack_hdeny_format.php/hostsdeny.txt', 'the-haleys.org ssh dictionary attacks', '#', ListType.BLACKLIST),
	('http://danger.rulez.sk/projects/bruteforceblocker/blist.php', 'danger.rulez.sk bruteforce blocklist', '#', ListType.BLACKLIST),
	('http://lists.blocklist.de/lists/all.txt', 'blocklist.de all blocked attackers', '#', ListType.BLACKLIST),
	('http://malc0de.com/bl/IP_Blacklist.txt', 'malc0de.com malicious IP', '#', ListType.BLACKLIST),
	('http://rules.emergingthreats.net/blockrules/compromised-ips.txt', 'ET compromised IPs', '#', ListType.BLACKLIST),
	('http://support.clean-mx.de/clean-mx/xmlphishing?response=alive&format=csv&fields=ip&domain=', 'clean-mx.de phishing', '#', ListType.BLACKLIST),
	('http://support.clean-mx.de/clean-mx/xmlviruses?response=alive&format=csv&fields=url,ip,domain&domain=', 'clean-mx.de viruses', '#', ListType.BLACKLIST),
	('http://vmx.yourcmc.ru/BAD_HOSTS.IP4', 'vmx.yourcmc.ru:pam_abl evil ssh hosts', '#', ListType.BLACKLIST),
	('http://www.autoshun.org/files/shunlist.csv', 'autoshun.org multiple malicious activities', '#', ListType.BLACKLIST),
	('http://www.ciarmy.com/list/ci-badguys.txt', 'ciarmy.com badguys', '#', ListType.BLACKLIST),
	('http://www.infiltrated.net/blacklisted', 'infiltrated.net blacklist', '#', ListType.BLACKLIST),
	('http://www.malwaredomainlist.com/hostslist/ip.txt', 'malwaredomainlist.com blocklist', '#', ListType.BLACKLIST),
	('http://www.openbl.org/lists/base.txt', 'OpenBL.org blocklist', '#', ListType.BLACKLIST),
	('http://www.spamhaus.org/drop/drop.txt', 'spamhaus drop rule', ';', ListType.BLACKLIST),
	('http://www.spamhaus.org/drop/edrop.txt', 'spamhaus edrop rule', ';', ListType.BLACKLIST),
	('http://www.t-arend.de/linux/badguys.txt', 't-arend.de badguys', '#', ListType.BLACKLIST),
	('https://feodotracker.abuse.ch/blocklist/?download=ipblocklist', 'abuse.ch Feodo blocklist', '#', ListType.BLACKLIST),
	('https://palevotracker.abuse.ch/blocklists.php?download=ipblocklist', 'abuse.ch Palevo blocklist', '#', ListType.BLACKLIST),
	('https://reputation.alienvault.com/reputation.generic', 'alienvault.com reputation', '#', ListType.BLACKLIST),
	('https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt', 'ET Shadowserver C&C', '#', ListType.BLACKLIST),
	('https://spyeyetracker.abuse.ch/blocklist.php?download=ipblocklist', 'abuse.ch SpyEye blocklist', '#', ListType.BLACKLIST),
	('https://sslbl.abuse.ch/blacklist/sslipblacklist.csv', 'abuse.ch SSL Blacklist', '#', ListType.BLACKLIST),
	('https://www.dshield.org/block.txt', 'dshield blacklisted IP', '#', ListType.BLACKLIST),
	('https://www.dshield.org/ipsascii.html', 'dshield suspect IP', '#', ListType.BLACKLIST),
	('http://www.projecthoneypot.org/list_of_ips.php?t=d', 'projecthoneypot.org TOP25 Dictionary Attack', '#', ListType.BLACKLIST),
	('http://www.projecthoneypot.org/list_of_ips.php?t=h', 'projecthoneypot.org TOP25 Harvester', '#', ListType.BLACKLIST),
	('http://www.projecthoneypot.org/list_of_ips.php?t=p', 'projecthoneypot.org TOP25 Comment Spam', '#', ListType.BLACKLIST),
	('http://www.projecthoneypot.org/list_of_ips.php?t=s', 'projecthoneypot.org TOP25 Spam', '#', ListType.BLACKLIST),
	('https://zeustracker.abuse.ch/blocklist.php?download=badips', 'abuse.ch Zeus BadIP', '#', ListType.BLACKLIST),
	('https://zeustracker.abuse.ch/blocklist.php?download=ipblocklist', 'abuse.ch Zeus blocklist', '#', ListType.BLACKLIST),
]
# CURRENTLY DISABLED: http://exposure.iseclab.org/malware_domains.txt
# Interessant, HTML+Paging: http://www.malwareblacklist.com/showMDL.php, http://www.malwaregroup.com/ipaddresses

'''
https://www.dshield.org/feeds/suspiciousdomains_Low.txt
https://www.dshield.org/feeds/suspiciousdomains_Medium.txt
https://www.dshield.org/feeds/suspiciousdomains_High.txt

# URL (hxxp instead of http - replace)
http://www.blade-defender.org/eval-lab/blade.csv

More Blacklists @
 - https://code.google.com/p/collective-intelligence-framework/wiki/NewFeedSources
 - https://github.com/albgnz/ThreatIntelligence/blob/master/blocklists
 - http://zeltser.com/combating-malicious-software/malicious-ip-blocklists.html
'''

class HostClassifier:
	def __init__(self):
		self.alllists = [BlacklistReader(f,r,s,l) for f,r,s,l in blacklists]
		
	def getRisk(self, ip):
		count_all = 0
		good = []
		bad = []
		for l in self.alllists:
			count_all += 1
			r = l.getRisk(ip)
			if r:
				if r[0] > 0:
					good.append(r[1])
				elif r[0] < 0:
					bad.append(r[1])

		if len(good) > 0:
			return (ListType.WHITELIST, "Unsuspicious Host %s listed on %s" % (ip, ', '.join(good)))
		elif len(bad) > 0:
			return (-(len(bad)/count_all), "Suspicious Host %s listed on %s" % (ip, ', '.join(bad)))

		return (0.25, "Host %s seems ordinary." % ip) # "Im Zweifel für den Angeklagten"
		
class CountryClassifier:
	def __init__(self):
		pass
		
	def getRisk(self, ip):
		# @return -1 .. 0 (without +1 ?!)
		return 0