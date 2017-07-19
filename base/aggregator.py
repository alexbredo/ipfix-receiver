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

class ListAggregator():
	def __init__(self, mylist):
		self.mylist = mylist
		self.functions = {
			'min': self.min,
			'max': self.max,
			'sum': self.sum,
			'common': self.common,
			'first': self.first,
			'last': self.last
		}
		
	def __probability_distribution(self):
		c = len(self.mylist)
		return [(item, self.mylist.count(item) / c) for item in set(self.mylist)]

	def common(self):
		'''
		@return (value, probability)
		'''
		lastmax = 0
		lastmax_value = None
		for item, probability in self.__probability_distribution():
			if probability > lastmax:
				lastmax = probability
				lastmax_value = item
		#return (lastmax_value, probability)
		return lastmax_value
		
	def printHistogram(self):
		print ("Value   % Histogram:")
		for v,p in self.__probability_distribution():
			print ("%5s %3s %s" % (v, int(p*100), '#'*int(p*100)))
		
	def min(self):
		return min(self.mylist)
		
	def max(self):
		return max(self.mylist)
		
	def sum(self):
		return sum(self.mylist)
		
	def first(self):
		return self.mylist[0]
		
	def last(self):
		return self.mylist[-1]
		
	def aggregate(self, function):
		if function in self.functions:
			return self.functions[function]()
		else:
			raise Exception("Aggregationsfunktion für '%s' ist nicht implementiert. (Benutze: %s)" % (function, ', '.join(self.functions.keys())))
		
'''
la = ListAggregator([1,2,2,3])
print(la.aggregate('common'))
'''