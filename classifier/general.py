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

from classifier.ports import PortClassifier
from classifier.hosts import HostClassifier
from classifier.regularities import KnownPartners, KnownHost 

class SecurityAnalyzor:
	def __init__(self):
		self.hc = HostClassifier() # Prüft, ob das System auf einer bekannten schwarzen Liste steht.
		self.pc = PortClassifier() # Prüft das Risiko eines Ports (Bots, Trojaner, usw.)
		self.kh = KnownHost() # Stellt fest, ob der Kommunikationspartner schon bekannt ist
		self.kp = KnownPartners() # Stellt fest, ob eine Konversation schon mal stattgefunden hat
		# TODO: Netzwerkauslastung prüfen. Stufenweiser, dynamischer Schwellwert für NetLoad #20 50 100 1000
		
	def getRisk(self, src_ip, dst_ip, dst_port):
		# TODO: Anders bewerten -- so können Ereignisse untergehen, weil sie eine zu geringe Bwertung haben...
		result = [
			#(self.hc.getRisk(src_ip), 0.25),
			(self.hc.getRisk(dst_ip), 0.5),
			(self.pc.getRisk(dst_port), 0.2),
			#(self.kh.getRisk(src_ip), 0.1),
			(self.kh.getRisk(dst_ip), 0.15),
			(self.kp.getRisk(src_ip, dst_ip), 0.15),
		]
		
		#for r in result:
		#	print('DEBUG', r[0])
			
		return (sum([(r[0][0] * r[1]) for r in result]), '; '.join([r[0][1] for r in result]))
		
	def store(self):
		# self.hc.store() # Nothing to store
		# self.pc.store() # Nothing to store
		self.kh.store()
		self.kp.store()


# THRESHOLD
# >= 0: 		OK
# -0.5 .. 0: 	Gnade
# < -0.5:		Argh