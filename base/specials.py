'''
Areas of application: If you want to process data partially

Performance: 
	Not very cheap, because a lot of memory I/O,
	but probably cheaper, than processing all data ;-)
	
Better ideas welcome...
'''
class Sampler:
	def __init__(self, sample_percentage = 0.5):
		if sample_percentage <= 0 or sample_percentage > 1:
			raise Exception("sample_percentage must be in range ]0 to 1]")
			
		self.__counter = 0
		self.__n = int(1 / sample_percentage)
		
	# shouldBeProcessed() --> Every n-th request is True.
	
	# 10 Mio requests ~ 4 Sec. 
	# 100 Mio ~ 50 Sec.
	'''
	def shouldBeProcessed(self):
		self.__counter = (self.__counter + 1) % (self.__n + 1)
		if self.__counter == self.__n:
			self.__counter = 0
			return True
		return False
	'''
	
	# 10 Mio ~ 3 Sec.
	# 100 Mio ~ 43 Sec. (a little bit better)
	# Equivalent C++-Code would finish in < 1 sec. The time hast come to switch ;-)
	def shouldBeProcessed(self):
		self.__counter += 1
		if self.__counter >= self.__n:
			self.__counter = 0
			return True
		else:
			return False
		
		
'''
Example:

s = Sampler(0.1)

for i in range(0,100000000):
	s.shouldBeProcessed()
'''