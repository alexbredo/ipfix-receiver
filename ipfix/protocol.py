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

import ipaddress, struct
from ipfix.information_elements import information_elements
from ipfix.errors import NoTemplateException, InvalidProtocolException, ProtocolException
from base.interpreter import ByteInterpreter

class IPFIXProtocol():
	def __repr__(self):
		return "%s %s" % (type(self).__name__, {k: v for k, v in self.__dict__.items() if not k.startswith('_')}) # superclass: __class__.__name__

class Header(IPFIXProtocol):
	FORMAT = '!HHIII'
	
	def __init__(self, data):
		rawnd = struct.unpack(Header.FORMAT, data[:self.getLength()])
		self.version, self.length, self.timestamp, self.sequence, self.domain_id = rawnd
		if self.version != 10:
			raise InvalidProtocolException()
		
	def getLength(self):
		return struct.calcsize(Header.FORMAT)
		
class SetHeader(IPFIXProtocol):
	FORMAT = '!HH'
	
	def __init__(self, data, offset=16):
		rawnd = struct.unpack(SetHeader.FORMAT, data[offset:offset + self.getLength()])
		self.set_id, self.set_length = rawnd
		
	def getLength(self):
		return struct.calcsize(SetHeader.FORMAT)
		
class TemplateHeader(IPFIXProtocol):
	FORMAT = '!HH'
	
	def __init__(self, data, offset=20):
		rawnd = struct.unpack(TemplateHeader.FORMAT, data[offset:offset + self.getLength()])
		self.template_id, self.field_count = rawnd
		
	def getLength(self):
		return struct.calcsize(TemplateHeader.FORMAT)
	
class Template(IPFIXProtocol):
	def __init__(self, data, field_count, offset=24):
		self.fields = [] # List of Fields
		self.__format = '!' + ('HH' * field_count)
		rawnd = struct.unpack(self.__format, data[offset:offset + self.getLength()])
		for ie_id, length in zip(rawnd[0::2], rawnd[1::2]):
			field = dict()
			field['id'] = ie_id 
			field['length'] = length 
			field['caption'] = information_elements[ie_id]
			self.fields.append(field)
			
	def getLength(self):
		return struct.calcsize(self.__format)

from base.formatconversions import MacAddress
class Flow(IPFIXProtocol):
	def __init__(self, data, template, offset=20):
		self.__length = 0
		bi = ByteInterpreter(data)
		
		for field in template.fields:
			value = bi.getValue(offset, field['length'])
			self.__length += field['length']
			if field['caption'].endswith('IPv4Address'):
				setattr(self, field['caption'], ipaddress.ip_address(value))
			elif field['caption'].endswith('MacAddress'):
				setattr(self, field['caption'], str(MacAddress(value)))
			else:
				setattr(self, field['caption'], value)
			offset = offset + field['length'] # offset aktualisieren
			
			if offset > len(data):
				raise ProtocolException('Offset is greater than length of Data.')
			
	def getLength(self):
		return self.__length

# Cache IPFIX-Templates by Exporter and it's Template-ID
class StatefulTemplateManager():
	def __init__(self):
		self.data = dict()
		
	def process(self, template_id, exporter_ip, template):
		if exporter_ip not in self.data:
			self.data[exporter_ip] = dict()
		if template_id not in self.data[exporter_ip]:
			self.data[exporter_ip][template_id] = template
			
	def get(self, template_id, exporter_ip):
		try:
			return self.data[exporter_ip][template_id]
		except KeyError:
			return None
		

stm = StatefulTemplateManager()
class IPFIXReader():
	def __init__(self, request, exporter):
		self.header = Header(request)
		offset = self.header.getLength()
		self.flowdata = []
		self.exporter = exporter
		
		while offset < self.header.length:
			s = SetHeader(request, offset)
			
			if s.set_id == 2: # Data Template
				th = TemplateHeader(request, offset + s.getLength())
				stm.process(th.template_id, exporter, Template(request, th.field_count, offset + th.getLength() + s.getLength()))
			else: # Data
				template = stm.get(s.set_id, exporter)
				if template:
					default_msg_length = 1 # Length of first Message unknown yet (reason for workaround: msg-end could be padding)
					while (offset + default_msg_length) < self.header.length:
						flow = Flow(request, template, offset + s.getLength())
						flow.exporter = self.exporter
						self.flowdata.append(flow)
						default_msg_length = flow.getLength()
						offset = offset + flow.getLength()
					#print(" -- FLOW DATA RECEIVED -- ", self.header, offset + s.getLength())
				else: 
					raise NoTemplateException()
			offset = offset + s.set_length
	
	def getHeader(self):
		return self.header
		
	def getFlows(self):
		return self.flowdata
		
	def getFlowsWithHeader(self):
		result = []
		for flow in self.getFlows():
			newdict = self.header.__dict__.copy()
			newdict.update(flow.__dict__)
			result.append({k: v for k, v in newdict.items() if not k.startswith('_')})
		return result


