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

from base.applog import *
import urllib.request
from urllib.error import HTTPError

class ElasticsearchClient():
	def __init__(self, host='127.0.0.1', port=9200, index='default', doctype='doc'):
		self.index = index
		self.doctype = doctype
		self.host = host
		self.port = port
		#self.setup()
		
	def setup(self):
		if not self.__exists_index():
			log.info("Elasticsearch-Index '%s' does not exist. Trying to create now." % self.index)
			self._create_index_mapping()
			log.info("Elasticsearch-Index '%s' was created." % self.index)
		else:
			log.info("Elasticsearch-Index '%s' present." % self.index)
		
	def saveOne(self, data):
		# POST /index/type/
		example = '''{
			"tweet" : {
				"user" : "kimchy",
				"post_date" : "2009-11-15T14:12:12",
				"message" : "trying out Elasticsearch"
			}
		}'''
		raise Exception("NotImplementedYet")
		

		
	def saveMany(self, data, doctype):
		log.debug("Trying to save %d items to Elasticsearch." % len(data))
		serialized_data = [self.__makeStringsFromDict(x) for x in data]
		return self.__bulkJSON(serialized_data, doctype)
	
	def __makeStringsFromDict(self, dictionary):
		try:
			for key in dictionary.keys():	# Native Datatypes: No Objects!
				if isinstance(dictionary[key], dict): # nested...
					dictionary[key] = self.__makeStringsFromDict(dictionary[key])
				elif not isinstance(dictionary[key], str) and not isinstance(dictionary[key], int) and not isinstance(dictionary[key], float):
					dictionary[key] = dictionary[key].__str__()
			return dictionary
		except Exception as e:
			log.error(e)

	def deleteIndex(self):
		request = urllib.request.Request('http://%s:%i/%s/' % (self.host, self.port, self.__getDailyIndex()))
		request.get_method = lambda: 'DELETE'
		res = urllib.request.urlopen(request)
		log.info("Elasticsearch-Index '%s' was removed." % self.index)
		
	def __bulkJSON(self, bulkdata, doctype):
		try:
			head = ({ "index" : { "_index" : self.__getDailyIndex(), "_type" : doctype } }).__str__() + '\n'
			dataAsStr = ('\n'.join([head + line.__str__() for line in bulkdata])).replace('\'', '\"') + '\n'
			req = urllib.request.Request(
				'http://%s:%i/%s/%s/_bulk' % (self.host, self.port, self.__getDailyIndex(), doctype),
				dataAsStr.encode("utf8"),
				headers={'Content-Type':'application/json'}
			)
			res = urllib.request.urlopen(req)
			return res.read().decode("utf8")
			if res.status != 200:
				raise Exception(res.read().decode("utf8"))
		except HTTPError as e:
			raise Exception(e.read().decode("utf8"))
			
	def __exists_index(self):
		try:
			req = urllib.request.Request(
				'http://%s:%i/%s/_mapping' % (self.host, self.port, self.__getDailyIndex()),
				headers = {'Content-Type':'application/json'}
			)
			res = urllib.request.urlopen(req)
			#print( res.read().decode("utf8"))
			return True
		except HTTPError:
			return False
		
	
	def _create_index_mapping(self, ttl='3d'):
		# POST /index/
		data = '''{
			"mappings" : {
				"_default_" : {
					"_ttl": {
					   "enabled": true,
					   "default": "%s"
					},
					"properties" : {
						"sourceIPv6Address": { "type": "string", "index": "not_analyzed" },
						"destinationIPv6Address": { "type": "string", "index": "not_analyzed" },
						"sourceHostname" : {"type" : "string", "index" : "not_analyzed"},
						"destinationHostname" : {"type" : "string", "index" : "not_analyzed"},
						"destinationTransportPortName" : {"type" : "string", "index" : "not_analyzed"},
						"sourceTransportPortName" : {"type" : "string", "index" : "not_analyzed"},
						"protocolIdentifierName" : {"type" : "string", "index" : "not_analyzed"},
						"networkLocation" : {"type" : "string", "index" : "not_analyzed"},
						"securityReason" : {"type" : "string", "index" : "not_analyzed"}
					}
				}
			}
		}''' % ttl
		res = urllib.request.urlopen(urllib.request.Request(
			'http://%s:%i/%s/' % (self.host, self.port, self.__getDailyIndex()),
			data.encode("utf8"),
			headers = {'Content-Type':'application/json'}
		))
		return res.read().decode("utf8")

	def __getDailyIndex(self):
		import time
		return "%s-%s" % (self.index, time.strftime("%Y.%m.%d"))
	
'''
if __name__ == '__main__':
	ec = ElasticsearchClient('lnx06-elasticsearch2', 9200, 'temporary')
	print(ec.bulkJSON([{'ab':1, 'cd':'blub'}, {'ddd':22, 'dfd':'fdgg'}]))
'''
