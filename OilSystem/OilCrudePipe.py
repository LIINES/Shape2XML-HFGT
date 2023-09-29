"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

import xml.etree.ElementTree as ET
from collections import OrderedDict

class OilCrudePipe(object):
	def __init__(self):
		self.name = 'Crude Oil Pipe'
		self.type = 'OilCrudePipe'
		self.fBus = None
		self.tBus = None
		self.maxP = None
		self.minP = None
		self.minQ = None
		self.maxQ = None
		self.lineName = None
		self.refinement = None
		self.fuelType = None
		self.status = None

		self.coordinate = None
		self.clust_origin = ''
		self.clust_dest = ''
		self.joined = set()
		self.controller = []

	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def get_status(self):
		return self.status

	def get_origin(self):
		return self.fBus

	def get_dest(self):
		return self.tBus

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the crude oil pipeline object with functionality.
		"""
		transporter = ET.SubElement(parent, 'Transporter', OrderedDict([('name', self.lineName),('controller',', '.join(self.controller))]))
		for k1 in self.refinement:
			method_port1 = ET.SubElement(transporter, 'MethodxPort', OrderedDict([('name', 'transport'), ('status', 'true'), ('origin', self.fBus), ('dest', self.tBus), ('operand',k1), ('output',k1), ('ref', k1)]))
			method_port2 = ET.SubElement(transporter, 'MethodxPort', OrderedDict([('name', 'transport'), ('status', 'true'), ('origin', self.tBus), ('dest', self.fBus), ('operand',k1), ('output',k1), ('ref', k1)]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the crude oil pipeline object with functionality.
		"""
		resource = sum(resourceCount)
		for k1 in self.refinement:
			method_port1 = ET.SubElement(parent, 'MethodxPort', OrderedDict(
				[('resource', str(resource)), ('name', 'transport'), ('status', 'true'), ('origin', str(resourceIdx[self.fBus])), ('dest', str(resourceIdx[self.tBus])), ('operand', k1),
				 ('output', k1), ('ref', k1),('controller',', '.join(self.controller))]))
			method_port2 = ET.SubElement(parent, 'MethodxPort', OrderedDict(
				[('resource', str(resource)), ('name', 'transport'), ('status', 'true'), ('origin', str(resourceIdx[self.tBus])), ('dest', str(resourceIdx[self.fBus])), ('operand', k1),
				 ('output', k1), ('ref', k1),('controller',', '.join(self.controller))]))

		resourceCount[2] += 1
		resourceIdx[self.lineName] = resource
		return resourceCount