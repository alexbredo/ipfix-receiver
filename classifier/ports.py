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

'''
from base.database import DatabaseTable

class PortClassifier():
	def __init__(self):
		self.db = DatabaseTable([('port', 'int'), ('bad', 'int'), ('good', 'int'), ('classifier', 'real'), ('label', 'text')], 'ports', 'ports')
		
	def getRisk(self, port):
		# @return (-1 .. 1, reason)
		#	-1: definitly bad
		#	0: don't know
		#	+1: definitly good
		#	Usage: Threshold -1.00 to -0.90 (?)
		condition = "port = %s" % port
		r = self.db.select(['classifier','label'], condition)
		if r:
			return (float(r[0][0].replace(',', '.')), r[0][1]) # Return first Element 
			
		return 0
		
	# TODO: Rate High-Ports better ... (?)
'''

import os, pickle

class PortClassifier():
	PORT_FILE = 'sec.ports.data'
	
	def __init__(self):
		self.data = dict()
		if os.path.isfile(PortClassifier.PORT_FILE):
			self.data = pickle.load(open(PortClassifier.PORT_FILE, "rb"))
		else:
			raise Exception('Port-Data-File not found: %s' % PortClassifier.PORT_FILE)
		
	def getRisk(self, port):
		'''
		@return (-1 .. 1, reason)
			-1: definitly bad
			0: don't know
			+1: definitly good
			Usage: Threshold -1.00 to -0.90 (?)
		'''
		if port in self.data:
			value = self.data[port][0]
			reason = "%s port %s: %s." % (self.__getCategory(value), port, self.data[port][1])
			return (value, reason)
		return (0.25, 'Port %s not known.' % port) # Im Zweifel für den Angeklagten
		
	def __getCategory(self, value):
		if value < -0.33:
			return "suspicious"
		elif value > 0.33:
			return "unsuspicious"
		return "ordinary"

#pc = PortClassifier()
#for x in range(0,1000):
#	print(pc.getRisk(80))