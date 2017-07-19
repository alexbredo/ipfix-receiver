import os
import uuid
import pickle

class DelayedWriter:
	def __init__(self, directory, count=100):
		self.data = []
		self.count = count
		self.directory = directory
	
	def put(self, item):
		self.data.append(item)
		if len(self.data) > self.count:
			self.__write()
			self.data = []
			
	def __write(self):
		filename = os.path.join(self.directory, str(uuid.uuid1())) # Random Filename based on Hostname + Time
		pickle.dump(self.data, open(filename, "wb"))