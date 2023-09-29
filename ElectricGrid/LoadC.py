#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

from ElectricGrid.ElectricNode import ElectricNode
import xml.etree.ElementTree as ET
from collections import OrderedDict

class LoadC(ElectricNode):
	"""
	This class represents electric grid loads.

	Attributes:
		loadCType   type of load
		maxP        maximum power demand
		minP        minimum power demand
		maxQ        maximum reactive power demand
		minQ        minimum reactive power demand
		rNode
		xNode
		nodeType    returns the a string of the class name
	"""

	def __init__(self):
		"""
		This function creates an instance of the class with all attributes instantiated to None.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.loadName = None
		self.maxP = None
		self.minP = None
		self.maxR = None
		self.minR = None
		self.maxQ = None
		self.minQ = None
		self.rNode = None
		self.xNode = None
		self.loadCNum = None
		self.loadCType = None
		self.startUpC = None
		self.shutDnC = None
		self.linearC = None
		self.fixedC = None
		self.quadC = None
		self.status1 = None
		self.status2 = None
		self.maxP1 = None
		self.minP1 = None
		self.maxR1 = None
		self.minR1 = None
		self.maxP2 = None
		self.minP2 = None
		self.maxR2 = None
		self.minR2 = None
		self.controller = []

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the LoadC object with functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.loadName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'consume electric power'), ('operand', 'electric power at 132kV'), ('output', ''),('status','true')]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', self.loadName), ('dest', self.loadName), ('ref', 'electric power at 132kV'),('status','true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the LoadC object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'consume electric power'), ('operand', 'electric power at 132kV'), ('output', ''),
			 ('status', 'true'), ('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'electric power at 132kV'),
			 ('status', 'true'), ('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.loadName] = resource
		return resourceCount, resourceIdx