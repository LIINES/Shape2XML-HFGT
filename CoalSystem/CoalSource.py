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

class CoalSource(ElectricNode):
	"""
	This class represents all coal systems controllable sources.

	Attributes:
		sourceNum     	source number (positive integer)
		sourceName    	source name
		nodeName		node name
		sourceClass   	source class
		maxCoal       	maximum coal output
		minCoal       	minimum Coal output
		fuelType      	Fuel Source type
		status      	machine status, >0 = machine in-service, 0 = machine out-of-service
		cluster			cluster node belongs too

	"""

	def __init__(self):
		"""
		This class creates an instance of the source class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.sourceNum = None
		self.sourceName = None
		self.sourceClass = None
		self.maxCoal = None
		self.minCoal = None
		self.fuelType = None
		self.status = None
		self.cluster = None
		self.controller = []

	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the source object with functionality.
		"""

		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import coal'), ('operand',''),('output', 'coal'), ('status',self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'coal'), ('output', 'coal'),('origin', self.nodeName), ('dest', self.nodeName), ('ref', 'coal'),('status', self.status)]))

	def add_xml_child_hfgt_dofs(self,parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the source object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'import coal'), ('operand', ''), ('output', 'coal'), ('status', self.status), ('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'coal'), ('output', 'coal'), ('origin', str(resource)),
			 ('dest', str(resource)), ('ref', 'coal'), ('status', self.status), ('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.nodeName] = resource
		return resourceCount, resourceIdx
