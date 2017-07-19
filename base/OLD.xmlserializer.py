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

from xml.etree.ElementTree import ElementTree
import xml.etree.ElementTree as ET

# Handle Natives, Lists, Dicts, Tuples. But not Objects. 
class Serializable(): 
	def __init__(self, filename='config.xml'):
		self._filename = filename
		
	def save(self):
		root = ET.Element('appconfig')
		for k,v in self.__dict__.items():
			self.__handleAnything(k,v,root)
		#ET.dump(root) # DEBUG
		ElementTree(root).write(self._filename, encoding='utf-8', xml_declaration=True)
		
	def __handleAnything(self, k, value, root):
		if k.startswith('_'):
			return
		
		parent = ET.SubElement(root, type(value).__name__)
		parent.set('name', k)
		#print ("Type:", type(value).__name__)
		if isinstance(value, (str,int,float,bool)):
			parent.text = str(value)
			return parent.text
		elif isinstance(value, list):
			self.__handleList(value, parent)
		elif isinstance(value, dict):
			self.__handleDict(value, parent)
		elif isinstance(value, tuple):
			self.__handleTuple(value, parent)
		elif not value:
			pass # NoneType
			return None
		else:
			raise Exception("Unhandled Type: %s" % type(value).__name__)
	
	def __handleDict(self, value, parent):
		for dk,dv in value.items():
			if isinstance(dv, (str,int,float)):
				li = ET.SubElement(parent, type(dv).__name__)
				li.set('name', dk)
				li.text = str(dv)
			else: # Subhandler
				self.__handleAnything(dk, dv, parent)

	def __handleList(self, value, parent):
		for item in value:
			if isinstance(item, (str,int,float)):
				li = ET.SubElement(parent, type(item).__name__)
				li.text = str(item) 
			else: # Subhandler
				self.__handleAnything('temp', item, parent)
			
	def __handleTuple(self, value, parent):
		for item in value:
			if isinstance(item, (str,int,float)):
				li = ET.SubElement(parent, type(item).__name__)
				li.text = str(item) 
			else: # Subhandler
				self.__handleAnything('temp', item, parent)
		
	def load(self):
		tree = ElementTree()
		tree.parse(self._filename)
		root = tree.getroot()
		if root.tag == 'appconfig':
			for child in root:
				setattr(self, child.get('name'), self.__xmlHandleAnything(child))
			
	def __xmlHandleAnything(self, child):
		if child.tag == 'int':
			return int(child.text)
		elif child.tag == 'float':
			return float(child.text)
		elif child.tag == 'str':
			return str(child.text)
		elif child.tag == 'bool':
			return child.text == 'True'
		elif child.tag == 'tuple':
			return tuple(self.__xmlHandleAnything(item) for item in child)
		elif child.tag == 'list':
			return [self.__xmlHandleAnything(item) for item in child]
		elif child.tag == 'dict':
			return dict((item.get('name'), self.__xmlHandleAnything(item)) for item in child)
		elif child.tag == 'NoneType':
			return None
		else:
			raise Exception("Unhandled Type: %s" % child.tag)

#c = Serializable('test.xml')
#c.save()
#c.load()
#c.save()
#print(c.__dict__)