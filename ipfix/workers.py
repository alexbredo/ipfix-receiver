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

from multiprocessing import Process, Pool, Queue, current_process
from queue import Empty
import time
from base.appconfig import Configuration
from base.applog import *
from ipfix.protocol import IPFIXReader
from ipfix.errors import ProtocolException


from enum import Enum
class QueueEnum(Enum):
	Start = 0
	Flow = 1
	Corrector = 2
	Conversation = 4 
	Stats = 8
	Security = 16
	Postprocessing = 32
	Output = 64 

import random 
class QueueDirector:
	def __init__(self, flow_log_interval = 10):
		self.queues = dict()
		self.queues[QueueEnum.Start] = { 'queues': [], 'successor': [ QueueEnum.Flow ] }
		self.queues[QueueEnum.Flow] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Corrector ] }
		self.queues[QueueEnum.Corrector] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Conversation ] }
		self.queues[QueueEnum.Conversation] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Security ] }
		# Stats temporary disabled
		# self.queues[QueueEnum.Conversation] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Stats, QueueEnum.Security ] }
		self.queues[QueueEnum.Stats] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Output ] }
		self.queues[QueueEnum.Security] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Postprocessing ] }
		self.queues[QueueEnum.Postprocessing] = { 'queues': [ Queue() ], 'successor': [ QueueEnum.Output ] }
		self.queues[QueueEnum.Output] = { 'queues': [ Queue() ], 'successor': [] }
		self.flow_log_interval = flow_log_interval
		self.flow_count = 0
		self.counter_accesstime = time.time()
		
	def __mergeQueueInfo(self, k, v):
		return "%s: %s" % (k,v)
	
	def putFlow(self, me, element, identifier = 0):
		if me not in self.queues:
			raise Exception('QueueDirector does not know %s.' % str(me))
		else:
			if me == QueueEnum.Flow:
				self.flow_count += 1
				if self.flow_log_interval != 0:
					if (time.time() - self.counter_accesstime) >= self.flow_log_interval:
						details = '; '.join([self.__mergeQueueInfo(str(k).replace('QueueEnum.', ''), sum([q.qsize() for q in v['queues']])) for k,v in self.queues.items()])
						log.info('Flows per second: %s. Elements in Queue: %s (%s)' % (round(self.flow_count / self.flow_log_interval, 2), self.getOverallLength(), details))
						self.flow_count = 0
						self.counter_accesstime = time.time()
			for q in self.queues[me]['successor']:
				qnum = (identifier % len(self.queues[q]['queues'])) # -1 ? (weil zustandsbehaftet)
				self.queues[q]['queues'][qnum].put(element)
		
	def getFlow(self, me):
		if me not in self.queues:
			raise Exception('QueueDirector does not know %s.' % str(me))
		
		return random.choice(self.queues[me]['queues']).get()
		
	def getOverallLength(self):
		size = 0
		for key,value in self.queues.items():
			for q in value['queues']:
				size += q.qsize()
		return size
		

class GenericProcess(Process):
	def __init__(self, queue_director):
		self.queue_director = queue_director
		super(GenericProcess, self).__init__()
		self.enabled = True
		log.info("Process '%s' initialized." % self._name)
		self.__protocol_error_occured_once = False

	def stop(self):
		self.enabled = False

	def beforeStop(self):
		# Do some work on exit
		pass
		
	def run(self):
		while self.enabled:
			try:
				self.handle()
			except Empty:
				pass
			except KeyboardInterrupt:
				self.enabled = False
				log.info("%s has been stopped." % self._name)
			except ProtocolException as e:
				if not self.__protocol_error_occured_once:
					self.__protocol_error_occured_once = True
					log.error(e)
			except NoTemplateException:
				pass
			except Exception as e:
				log.error(e)


from ipfix.errors import NoTemplateException
class FlowConsumer(GenericProcess):
	def __init__(self, queue_director):
		self.has_ipfix_arrived = False
		super(FlowConsumer, self).__init__(queue_director)
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		requestObject, client_addr = self.queue_director.getFlow(QueueEnum.Flow)
		ipfix = IPFIXReader(requestObject, client_addr)
		for flow in ipfix.getFlowsWithHeader():
			self.queue_director.putFlow(QueueEnum.Flow, flow)
			
		if not self.has_ipfix_arrived:
			log.info('Congratulation: First flow has arrived.')
			self.has_ipfix_arrived = True
			
				
from iana.protocol import *
from network.subnets import LocationClassifier
class CorrectorConsumer(GenericProcess):
	def __init__(self, queue_director, ipfix_extreme_network_patch=False, conversation_consumer_threads = 2):
		self.ipfix_extreme_network_patch = ipfix_extreme_network_patch
		self.conversation_consumer_threads = conversation_consumer_threads
		self.locl = LocationClassifier()
		super(CorrectorConsumer, self).__init__(queue_director)
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		element = self.queue_director.getFlow(QueueEnum.Corrector)
		
		if 'sourceTransportPort' in element:
			element['sourceTransportPortName'] = serviceNum2Name(element['sourceTransportPort'])
		if 'destinationTransportPort' in element:
			element['destinationTransportPortName'] = serviceNum2Name(element['destinationTransportPort'])
		if 'protocolIdentifier' in element:
			element['protocolIdentifierName'] = transportNum2Name(element['protocolIdentifier'])
		
		if 'flowDurationMilliseconds' not in element:
			element['flowDurationMilliseconds'] = self.__getFlowDurationMilliseconds(element)
			#print(element)
		if 'exportInterface' not in element:
			element['exportInterface'] = None
		elif element['exportInterface'] is not None:
			if element['exportInterface'] >= 10000: 
				''' 
				@Bugfix: Many errornous interfaces (Range up to 4 Mrd.) 
				RFC5102-Datatype: unsigned32 (0 to 4294967295)
				[Optional] I  want to have only a small number of interfaces, because Routers have usually a small number of physical interfaces. Possible bug of routers ipfix implementation ... (Recheck required)
				'''
				log.warning("Received IPFIX-Message with an unusual Export-Interface (OutOfRange: %i > 10000). Export-Interface treated as None." % element['exportInterface'])
				element['exportInterface'] = None
			
		# socketIdentifier for distinct conversations:
		element['socketIdentifier'] = self.__getSocketIdentifier(element)
		
		# Lookup Location
		if 'sourceIPv4Address' in element:
			element['sourceNetworkLocation'] = self.locl.getLocation(str(element['sourceIPv4Address']))
		else:
			element['sourceNetworkLocation'] = 'unknown'
		if 'destinationIPv4Address' in element:
			element['destinationNetworkLocation'] = self.locl.getLocation(str(element['destinationIPv4Address']))
		else:
			element['destinationNetworkLocation'] = 'unknown'
		
		# Same conversations in same Queue (but separate processes):
		id = self.__getHash(element, self.conversation_consumer_threads)
		self.queue_director.putFlow(QueueEnum.Corrector, element, id)
				
	def __getFlowDurationMilliseconds(self, flow):
		flowStartSysUpTime = flow['flowStartSysUpTime']
		flowEndSysUpTime = flow['flowEndSysUpTime']
		if self.ipfix_extreme_network_patch:
			# This is a workaround, because Extreme Network don't know that 1s = 1000ms (!)
			# Achtung: Nur bei EXTREME 2^16, sonst 2^32 (!)
			if flowStartSysUpTime < flowEndSysUpTime:
				return (flowEndSysUpTime - flowStartSysUpTime) * 10
			else: # flowStartSysUpTime > flowEndSysUpTime:
				return ((flowEndSysUpTime + 65536) - flowStartSysUpTime) * 10
		else:
			if flowStartSysUpTime < flowEndSysUpTime:
				return (flowEndSysUpTime - flowStartSysUpTime) 
			else: # flowStartSysUpTime > flowEndSysUpTime:
				return ((flowEndSysUpTime + 4294967296) - flowStartSysUpTime)
				
	def __getSocketIdentifier(self, flow):
		# Layer 3 Connection
		if 'sourceIPv4Address' in flow and 'destinationIPv4Address' in flow and 'sourceTransportPortName' in flow and 'destinationTransportPortName' in flow:
			socketSource = flow['sourceIPv4Address'].__str__() + ':' + flow['sourceTransportPortName']
			socketDestination = flow['destinationIPv4Address'].__str__() + ':' + flow['destinationTransportPortName']
			if socketSource < socketDestination:
				return "%s-%s" % (socketSource, socketDestination)
			else:
				return "%s-%s" % (socketDestination, socketSource)
		# Layer "2" Connection
		elif 'sourceMacAddress' in flow and 'destinationMacAddress' in flow:
			if flow['sourceMacAddress'] < flow['destinationMacAddress']:
				return "%s-%s" % (flow['sourceMacAddress'], flow['destinationMacAddress'])
			else:
				return "%s-%s" % (flow['destinationMacAddress'], flow['sourceMacAddress'])
		# else physical? currently not supported.
		
	def __getHash(self, flow, max_thread_count = 1):
		if 'sourceIPv4Address' in flow and 'destinationIPv4Address' in flow:
			return (hash(flow['sourceIPv4Address']) + hash(flow['destinationIPv4Address']))
		else:
			return 0

			
from ipfix.conversation_aggregator import OpenSocketAggregator
class ConversationConsumer(GenericProcess):
	def __init__(self, queue_director, threadIdMapping, ttl_response_received=5, ttl_no_response=10): 
		self.osa = OpenSocketAggregator(ttl_response_received, ttl_no_response)
		self.last_cache_access = time.time()
		self.threadIdMapping = threadIdMapping
		super(ConversationConsumer, self).__init__(queue_director)
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		element = self.queue_director.getFlow(QueueEnum.Conversation)
		
		self.osa.process(element) # Flows verarbeiten
		
		if self.last_cache_access + 1 < time.time(): # Nur einmal pro Sekunde abholen und speichern ... (Performance sparen)
			self.last_cache_access = time.time() # Zeit aktualisieren
			conv = self.osa.getItemsOutOfTTL()
			if conv:
				self.queue_director.putFlow(QueueEnum.Conversation, conv)



from classifier.general import SecurityAnalyzor
from base.specials import Sampler
class SecurityConsumer(GenericProcess):
	def __init__(self, queue_director, sample_percentage, bypass = True):
		self.sampler = Sampler(sample_percentage)
		self.bypass = bypass
		if not self.bypass:
			log.info("Security Module enabled.")
			self.sa = SecurityAnalyzor()
		super(SecurityConsumer, self).__init__(queue_director)
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		conversations = self.queue_director.getFlow(QueueEnum.Security)
		
		if not self.bypass:
			for c in conversations:
				if 'sourceIPv4Address' in c and 'destinationIPv4Address' in c:
					if self.sampler.shouldBeProcessed(): # selective processing
						r = self.sa.getRisk(str(c['sourceIPv4Address']), str(c['destinationIPv4Address']), c['destinationTransportPort'])
						c['securityValue'] = r[0]
						c['securityReason'] = r[1]
		self.queue_director.putFlow(QueueEnum.Security, conversations)
				
	def beforeStop(self):
		# Store data on exit
		if not self.bypass:
			self.sa.store()
			
from network.dns import DNSCache
class PostprocessingConsumer(GenericProcess):
	def __init__(self, queue_director, dnscache):
		self.dnscache = dnscache 
		super(PostprocessingConsumer, self).__init__(queue_director)
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		element = self.queue_director.getFlow(QueueEnum.Postprocessing)

		conversationsWithHostnames = [self.__setHostnames(item) for item in element]

		self.queue_director.putFlow(QueueEnum.Postprocessing, (conversationsWithHostnames, 'conversation'))
				
	def __setHostnames(self, conversation):
		if 'sourceIPv4Address' in conversation and 'destinationIPv4Address' in conversation:
			conversation['sourceHostname'] = self.dnscache.getName(conversation['sourceIPv4Address'].__str__())
			conversation['destinationHostname'] = self.dnscache.getName(conversation['destinationIPv4Address'].__str__())
		return conversation
		
	def beforeStop(self):
		# Store data on exit
		self.dnscache.store()
		
				
from base.cache import IndexedTimeCache
class StatsConsumer(GenericProcess):
	IGNOREFIELDS = ['networkLocation', '@timestamp']
	
	def __init__(self, queue_director, ipfix_cache_seconds=30):
		self.stats_cache = IndexedTimeCache(ipfix_cache_seconds)
		self.last_cache_access = time.time()
		super(StatsConsumer, self).__init__(queue_director)
		
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		flows = self.queue_director.getFlow(QueueEnum.Stats)
		
		if not isinstance(flows, list):
			flows = [flows] # make list
			
		for flow in flows:
			if flow['sourceNetworkLocation'] and not flow['destinationNetworkLocation']: # Home to other network
				home_net = flow['sourceNetworkLocation']
				action = 'flow_request'
			elif flow['destinationNetworkLocation'] and not flow['sourceNetworkLocation']: # Other to home network
				home_net = flow['destinationNetworkLocation']
				action = 'flow_response'
			else: # Home to home, other to other (should not -- no network config)
				home_net = 'unknown'
				action = 'flow_request'
				
			for x in self.__getRemainingTimeData(flow, action, home_net):
				id = action + str(int(x['@timestamp']/10000)) + home_net  # 10-Sekunden Basis (sonst zu viele Datensätze!) + Standortunterscheidung + Richtung
				self.stats_cache.insert(id, x, StatsConsumer.IGNOREFIELDS)
			
		if self.last_cache_access + 1 < time.time(): # Nur einmal pro Sekunde abholen und speichern ... (Performance sparen)
			self.last_cache_access = time.time()
			
			stats = self.stats_cache.getItemsOutOfTTL() 
			if stats: 
				log.debug("Writeout %s stats to Elasticsearch." % (len(stats)))
				self.queue_director.putFlow(QueueEnum.Stats, (stats, 'stats'))

				
	def __getRemainingTimeData(self, flow, reqresname, networkLocation):
		# Generierte Pseudodatensätze, die die Flow-Menge über die Zeit verteilen. Realistischer, als hohe Peaks ... 
		remainList = []
		flowDuration = flow['flowDurationMilliseconds'] 
		timestamp = flow["timestamp"] # Anfangszeit der Konversation in Sek
		while flowDuration > 1000: # Nur wenn größer als 1 Sekunde, andernfalls sowieso schon gespeichert (im original flow)
			timestamp -= 1 # 1 Sekunde abziehen
			octetDeltaCountPerSec = round(flow['octetDeltaCount'] / (flow['flowDurationMilliseconds'] / 1000), 0)
			packetDeltaCountPerSec = round(flow['packetDeltaCount'] / (flow['flowDurationMilliseconds'] / 1000), 0)
			if octetDeltaCountPerSec == 0 and packetDeltaCountPerSec == 0:
				return []
			else:
				remainList.append({
					'@timestamp': timestamp * 1000, # in ms for ES
					'networkLocation': networkLocation,
					reqresname: {
						'octetDeltaCountPerSec': int(octetDeltaCountPerSec),
						'packetDeltaCountPerSec': int(packetDeltaCountPerSec)
					}
				})
			flowDuration -= 1000 # 1 Sekunde abziehen
		return remainList
		
from handler.elasticsearch import ElasticsearchClient
from handler.file import FileWriter
from handler.udpsender import UDPSender
class OutputConsumer(GenericProcess):
	def __init__(self, queue_director, enabled_handlers, elasticsearch, filename, udpreceiver):
		self.enabled_handlers = enabled_handlers
		if self.enabled_handlers['elasticsearch']:
			self.es_client = ElasticsearchClient(elasticsearch['host'], elasticsearch['port'], elasticsearch['index'])
			log.info("Saving to Elasticsearch enabled. Destination: http://%s:%s/%s" % (
				elasticsearch['host'], elasticsearch['port'], elasticsearch['index']
			))
		if self.enabled_handlers['file']:
			self.file_writer = FileWriter(filename)
			log.info("Saving to File enabled. Filename: %s" % filename)
		if self.enabled_handlers['screen']:
			log.info("Output to Screen (STDOUT) enabled.")
		if self.enabled_handlers['udpreceiver']:
			self.udpsender = UDPSender(udpreceiver['host'], udpreceiver['port']) 
			log.info("Output via UDP-Pickle enabled.")
		super(OutputConsumer, self).__init__(queue_director)
		
	def handle(self):
		log.debug('%s consuming.' %(self._name))
		bulk_data = self.queue_director.getFlow(QueueEnum.Output)
	

		if self.enabled_handlers['elasticsearch']:
			self.es_client.saveMany(bulk_data[0], bulk_data[1])
			log.debug("Writeout %i %s(s) to elasticsearch." % (len(bulk_data[0]), bulk_data[1]))
		if bulk_data[1] != 'stats':
			if self.enabled_handlers['file']:
				for conv in bulk_data[0]:
					self.file_writer.append(conv)
				log.debug("Writeout %i conversations to file." % len(bulk_data[0]))
			if self.enabled_handlers['screen']:
				for conv in bulk_data[0]:
					print(conv)
			if self.enabled_handlers['udpreceiver']:
				self.udpsender.send(bulk_data[0])
					

import os
import pickle
import time
class BackgroundWorker(GenericProcess):
	DIRECTORY = 'data/flows/'
	
	def __init__(self, queue_director, max_queue_size):
		self.max_queue_size = max_queue_size
		super(BackgroundWorker, self).__init__(queue_director)
		
	def handle(self):
		qs = self.queue_director.getOverallLength()
		if qs < int(self.max_queue_size / 3):
			files = os.listdir(BackgroundWorker.DIRECTORY)
			if len(files) >= 1:
				filename = os.path.join(BackgroundWorker.DIRECTORY, files[0]) # pick only one file
				log.info('%s consuming: %s.' % (self._name, filename))
				flows = pickle.load(open(filename, "rb")) # load file
				for flow in flows:
					self.queue_director.putFlow(QueueEnum.Start, flow) # put into initial queue
				os.remove(filename) # remove flow file
		time.sleep(5) # im 10 Sekunden Intervall ausführen, sonst nimmt der alle Dateien auf einmal!

		
from ipfix.misc import DelayedWriter
class Manager:
	def __init__(self):
		self.config = Configuration()
		self.queue_director = QueueDirector(self.config.flow_log_interval)
		self.dnscache = DNSCache(self.config.dns_cache_seconds)
		self.workers = []
		self.delayed_writer = DelayedWriter(BackgroundWorker.DIRECTORY, 1000)

	def start(self):
		# TODO: Evtl zuerst Prozesse initialisieren, dann Queue, Config laden, dann Prozesse starten (enable) --> Performance
		self.workers.append(FlowConsumer(self.queue_director)) # One Worker (Each Process needs each own IPFIX-Template!! Some Procs may never receive Templates!!!)
		for i in range(0, self.config.corrector_consumer_threads):
			self.workers.append(CorrectorConsumer(self.queue_director, self.config.ipfix_extreme_network_patch, self.config.conversation_consumer_threads))
		
		for i in range(0, self.config.conversation_consumer_threads):
			self.workers.append(ConversationConsumer(self.queue_director, i, 
				self.config.opensocketcache['ttl_no_response'],
				self.config.opensocketcache['ttl_response_received']
			))
		
		self.workers.append(PostprocessingConsumer(self.queue_director, self.dnscache))  # Multiple Workers (gemeinsames dict)
		self.workers.append(PostprocessingConsumer(self.queue_director, self.dnscache))
		self.workers.append(SecurityConsumer(self.queue_director, self.config.security_sample_percentage))
		self.workers.append(StatsConsumer(self.queue_director, 
			self.config.ipfix_cache_seconds
		))  # One Worker (because stateful: Timebased-Counter-Aggregator)
		self.workers.append(OutputConsumer(self.queue_director, 
			self.config.enabled_handlers, 
			self.config.elasticsearch, 
			self.config.filename,
			self.config.udpreceiver
		)) # Multiple Workers possible (2?).
		self.workers.append(BackgroundWorker(self.queue_director, self.config.queues_maxsize))

		for w in self.workers:
			w.start()
			
	def put(self, element):
		if self.queue_director.getOverallLength() <= self.config.queues_maxsize:
			self.queue_director.putFlow(QueueEnum.Start, element)
		else:
			self.delayed_writer.put(element)
			log.debug("Extremly long queue. IPFIX-Message flushed to disk (will be processed later).")
		
	def putNetflow(self, element):
		if self.queue_director.getOverallLength() <= self.config.queues_maxsize:
			self.queue_director.putFlow(QueueEnum.Flow, element)
		else:
			self.delayed_writer.put(element)
			log.debug("Extremly long queue. Netflow-Message flushed to disk (will be processed later).")

	def join(self):
		try:
			for w in reversed(self.workers):
				w.beforeStop()
				w.stop()
				w.terminate()
			del(self.workers)
		except KeyboardInterrupt:
			log.info("All processes were stopped.")
