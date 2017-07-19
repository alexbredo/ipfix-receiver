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
from multiprocessing import Lock

class IndexedTimeCache():
	'''
	@param ttl: Maxmimum Time to live for inserted item (first one will be applied)
	'''
	lock = Lock()
	
	def __init__(self, ttl=30):
		self.cache = dict()
		self.ttl = ttl
		
	def insert(self, index, data, ignore_fields=[]):
		IndexedTimeCache.lock.acquire() 
		if index in self.cache:	# UPDATE + AGGREGATE
			self.cache[index]['data'] = self.__aggregate(self.cache[index]['data'], data, ignore_fields)
		else: 					# NEW
			self.cache[index] = { 
				'timestamp': int(time.time()), # Insert Time
				'data': data 
			}
		IndexedTimeCache.lock.release() 
			
	def size(self):
		return len(self.cache)
		
	def getItemsOutOfTTL(self):
		IndexedTimeCache.lock.acquire() 
		cache_outofdate = dict()
		cache_new = dict()
		for k,v in self.cache.items():
			if v['timestamp'] < (time.time() - self.ttl):
				cache_outofdate[k] = v
			else:
				cache_new[k] = v
		self.cache = cache_new # Update Cache
		IndexedTimeCache.lock.release() 
		#print(len(cache_outofdate), len(cache_new))
		#print(cache_outofdate)
		#print(cache_new)
		return [item['data'] for item in cache_outofdate.values()]
		# cache_outofdate: dict_values([{'data': {'b': 1, 'a': 2, 'c': 4}, 'timestamp': 1403523219}, {...} ])
		# Return: [{'c': 2, 'b': 23, 'a': 25}, {'c': 2, 'b': 32, 'a': 29}, ...
		
	def __aggregate(self, old, new, ignore_fields):
		aggregated = old
		for key, value in new.items():
			if isinstance(value, dict):
				for sub_key, sub_value in value.items():
					if key in aggregated and (key not in ignore_fields or sub_key not in ignore_fields):
						if sub_key in aggregated[key]:
							aggregated[key][sub_key] += sub_value
						else:
							print("ERROR: Stats-Aggregation. Fields not found")
							#aggregated[key][sub_key] = dict()
							#aggregated[key][sub_key] = sub_value
					else:
						aggregated[key] = dict() #copy?
						print("ERROR: Stats-Aggregation. Fields not found")
			elif key not in ignore_fields:
				aggregated[key] += new[key]
		return aggregated

'''
import random
c = IndexedTimeCache(0)
for i in range(0,50):
	c.insert((int(time.time() - random.randint(1, 5))), { 'a': random.randint(1, 5), 'b': random.randint(1, 5), 'c': random.randint(1, 5) }, ['c'])

print(c.size())
print("====", c.getItemsOutOfTTL())
print(c.size())
'''

'''
c = IndexedTimeCache(0)
c.insert('123456789Hamburg', {
	"@timestamp": 123456789,
	"networkLocation": "Hamburg",
	"flow_request": {
		"packetDeltaCountPerSec": 30,
		"octetDeltaCountPerSec": 30,
		"flowDurationMilliseconds": 300
	}
})
c.insert('123456789Hamburg', {
	"@timestamp": 123456789,
	"networkLocation": "Hamburg",
	"flow_request": {
		"packetDeltaCountPerSec": 60,
		"octetDeltaCountPerSec": 60,
		"flowDurationMilliseconds": 600
	}
})
c.insert('123456789Hamburg', {
	"@timestamp": 123456789,
	"networkLocation": "Hamburg",
	"flow_request": {
		"packetDeltaCountPerSec": 20,
		"octetDeltaCountPerSec": 200,
		"flowDurationMilliseconds": 2000
	}
})
print(c.getItemsOutOfTTL())
'''