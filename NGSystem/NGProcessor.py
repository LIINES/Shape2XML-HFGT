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

class NGProcessor(ElectricNode):
	"""
	This class represents all NG Processors.

	Attributes:
		procNum     processor number (positive integer)
		procName    processor name
		procClass   processor class
		maxNG       maximum real natural gas output
		minNG       minimum real natural gas output
		fuelType	processing plant fuel type
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
		cluster		cluster processor belongs too
	"""

	def __init__(self):
		"""
		This class creates an instance of the NG processor class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.procNum = None
		self.procName = None
		self.procClass = None
		self.maxNG = None
		self.minNG = None
		self.fuelType = None
		self.status = None
		self.controller = []


	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the processor object with functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.procName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'process raw gas'), ('operand','raw gas'),('output', 'processed gas'), ('status',self.status)]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the processor object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'process raw gas'), ('operand', 'raw gas'), ('output', 'processed gas'),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		resourceCount[0] += 1
		resourceIdx[self.procName] = resource
		return resourceCount, resourceIdx