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

import time, math
# sort: http://stackoverflow.com/questions/72899/how-do-i-sort-a-list-of-dictionaries-by-values-of-the-dictionary-in-python
import operator
from base.aggregator import ListAggregator

class IPFIXConversation():
	
	def __init__(self, related_flows):
		self.related_flows = related_flows
		self.default_aggs = {
			'octetDeltaCount': 'sum', 
			'packetDeltaCount': 'sum', 
			'flowDurationMilliseconds': 'sum', 
			'timestamp': 'min',
			'flowStartSysUpTime': 'min',
			'flowEndSysUpTime': 'max'
		} 
		self.action1 = None
		self.action2 = None
		
	def getConversation(self):
		result = []
		action1_bucket = []
		action2_bucket = []
		for flow in self.related_flows:
			if flow['sourceIPv4Address'] == self.related_flows[0]['sourceIPv4Address']: # First Element is Pivot
				action1_bucket.append(flow)
			else:
				action2_bucket.append(flow)
		self.action1 = self.__aggregateFlows(action1_bucket)
		self.action2 = self.__aggregateFlows(action2_bucket)
		self.__bucketPostprocessing()
		return self.makeInfo()

	def makeInfo(self):
		flow = self.related_flows[0] # Reference Flow
		requiredFields = set(['sourceIPv4Address', 'destinationIPv4Address', 'exporter', 'exportInterface']) # anpassen (global)
		if requiredFields.issubset(set(flow.keys())):
			dnl = dict(flow) # copy
			dnl['@timestamp'] = int((flow["timestamp"] - (self.__getOverallDuration() / 1000)) * 1000) # ES needs timestamp in ms (!)
			dnl['responsetime'] = self.__getResponseTime()
			
			if self.action1 is not None:
				dnl['flow_request'] = self.action1 
			if self.action2 is not None:
				dnl['flow_response'] = self.action2 
			
			if (flow['sourceNetworkLocation'] is not None and flow['destinationNetworkLocation'] is not None) or flow['sourceNetworkLocation'] is not None:
				dnl['networkLocation'] = flow['sourceNetworkLocation']
			elif flow['destinationNetworkLocation'] is not None: # Cross-Switch (interchange)
				dnl['networkLocation'] = flow['destinationNetworkLocation']
				dnl['sourceIPv4Address'] = flow['destinationIPv4Address']
				dnl['destinationIPv4Address'] = flow['sourceIPv4Address']
				dnl['sourceTransportPort'] = flow['destinationTransportPort']
				dnl['sourceTransportPortName'] = flow['destinationTransportPortName']
				dnl['destinationTransportPort'] = flow['sourceTransportPort']
				dnl['destinationTransportPortName'] = flow['sourceTransportPortName']
				# http://stackoverflow.com/questions/15583032/nested-documents-in-elasticsearch
				if self.action1 is not None:
					dnl['flow_response'] = self.action1
				if self.action2 is not None:
					dnl['flow_request'] = self.action2
			else:
				dnl['networkLocation'] = 'unknown'
				
			# Cleanup (Remove aggregated fields)
			# del(dnl['sourceNetworkLocation'])
			# del(dnl['destinationNetworkLocation'])
			for k in self.default_aggs.keys():
				del(dnl[k])
			
			return dnl
		else:
			raise Exception ("Some fields missing: %s (for determining direction and network)" % ', '.join(requiredFields))
			
	def __getResponseTime(self):
		if not self.action1 and not self.action2:
			return 0 # unknown
			
		a = b = 0
		if self.action1:
			a = self.action1['timestamp']
		if self.action2:
			b = self.action2['timestamp']
		return int(math.fabs(int(b - a)))
		
	def __getOverallDuration(self):
		flow_duration = 0
		if self.action1:
			flow_duration += self.action1['flowDurationMilliseconds']
		if self.action2:
			flow_duration += self.action2['flowDurationMilliseconds']
		return flow_duration
			
	def __aggregateFlows(self, bucket):
		if not bucket:
			return None
		result = dict()
		result['flow_count'] = len(bucket)
		for field,function in self.default_aggs.items(): # TODO: all other fields: mostCommon (?)
			column = [flow[field] for flow in bucket]
			if column:
				la = ListAggregator(column)
				result[field] = la.aggregate(function)
		return result
		
	def __bucketPostprocessing(self):
		if self.action1:
			# Vorher wurden allen Werte unter 1000ms als "1000" ausgegeben - andernfalls schießen die Ergebnisse unnötig in die Höhe
			if self.action1['flowDurationMilliseconds'] > 1000:
				self.action1['octetDeltaCountPerSec'] = int(self.action1['octetDeltaCount'] / (self.action1['flowDurationMilliseconds'] / 1000))
				self.action1['packetDeltaCountPerSec'] = int(self.action1['packetDeltaCount'] / (self.action1['flowDurationMilliseconds'] / 1000))
			else:
				self.action1['octetDeltaCountPerSec'] = self.action1['octetDeltaCount']
				self.action1['packetDeltaCountPerSec'] = self.action1['packetDeltaCount'] 
		if self.action2:
			if self.action2['flowDurationMilliseconds'] > 1000:
				self.action2['octetDeltaCountPerSec'] = int(self.action2['octetDeltaCount'] / (self.action2['flowDurationMilliseconds'] / 1000))
				self.action2['packetDeltaCountPerSec'] = int(self.action2['packetDeltaCount'] / (self.action2['flowDurationMilliseconds'] / 1000))
			else:
				self.action2['octetDeltaCountPerSec'] = self.action2['octetDeltaCount']
				self.action2['packetDeltaCountPerSec'] = self.action2['packetDeltaCount'] 
		
'''
  Effizienz: 10000 Flows (7,5 Minuten) wurden zu 2065 Konversationen zusammengefasst. (Komprimierung um ~79%)
  Minimale Konversationszahl wäre 1383 (Host-to-Host Kommunikation) (=> Komprimierung um ~86%)
  Restliche 682 Flows müssen Anfragen ohne Anworten sein (Dead Requests) !?
   - bzw. die Flows wurden vor oder nach dem Zeitfenster behandelt (Sliding Window)
   - aber es gibt tatsächlich Flows, die keine Antwort haben! Dafür ist der Timeout besonders sinnvoll...
'''

class OpenSocketAggregator():
	# Jeder Exporter könnte eine eigene Instanz bekommen, für den Fall, dass zufällig irgendwelche Socket-Kollisionen entstehen (sehr sehr unwahrscheinlich)
	#WriteLock = threading.Lock() 
	
	def __init__(self, ttl_response_received=60, ttl_no_response=600): # TTL in Sekunden
		self.ttl_response_received = ttl_response_received
		self.ttl_no_response = ttl_no_response
		self.raw_flow_cache = dict()
		# ttl_no_response ttl_response_received
		# first n flows in learning mode? no decisions?
		# multiple intiator-flows? (paritionized)
		# Problematisch bei: TCP keepalive, UDP ohne Antworten. 
		self.__l3_error_occured_once = False # Temporary Workaround to surpress a lot of trash
		
	def cache_size(self):
		return len(self.raw_flow_cache)
	
	def process(self, data):
		# Nachteil: Keine saubere Socket2Socket Zuordnung (andernfalls ineffiziente Aggregation) - sich ständig ändernde High Ports sind in der Aussagekraft zu vernachlässigen
		#OpenSocketAggregator.WriteLock.acquire() 
		if 'sourceIPv4Address' in data and 'destinationIPv4Address' in data:
			socket = data['socketIdentifier']
			if socket not in self.raw_flow_cache: # Conversation-Initiator
				self.raw_flow_cache[socket] = {
					'bucket': [ data ],
					'timestamp': time.time() # zum aussortieren aus dem cache
				}
			else: # Conversation-Partner
				self.raw_flow_cache[socket]['bucket'].append(data)
		else:
			if self.__l3_error_occured_once:
				print ('INFO@OpenSocketAggregator: Ignoring flow, because not Layer 3 (IP).') # To be done: Create L2-Aggregator (MAC)
				self.__l3_error_occured_once = True
		#OpenSocketAggregator.WriteLock.release() 
	
	def __getTTLPerBucket(self, bucket):
		if 'flow_request' in bucket and 'flow_response' in bucket:
			return self.ttl_response_received
		return self.ttl_no_response
	
	def getItemsOutOfTTL(self):
		cache_outofdate = dict()
		cache_new = dict()
		conversations = []
		#OpenSocketAggregator.WriteLock.acquire()
		for k,v in self.raw_flow_cache.items():
			if v['timestamp'] <= (time.time() - min(self.ttl_response_received, self.ttl_no_response)): # TTL vorfiltern
				conv = IPFIXConversation(v['bucket']).getConversation()
				if v['timestamp'] <= (time.time() - self.__getTTLPerBucket(conv)):
					cache_outofdate[k] = v
					conversations.append(conv)
				else:
					cache_new[k] = v
			else:
				cache_new[k] = v
		self.raw_flow_cache = cache_new # Update Cache
		#OpenSocketAggregator.WriteLock.release() 
		#print("outofdate", len(cache_outofdate))
		#print("in cache ", len(cache_new))
		return conversations