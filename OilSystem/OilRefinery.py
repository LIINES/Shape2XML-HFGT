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

class OilRefinery(ElectricNode):
	"""
	This class represents all power systems controllable generators.

	Attributes:
		refNum     terminal number (positive integer)
		refName    generator name
		refClass   terminal class
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
		maxOil      maximum processed oil output
		minOil      minimum processed oil output
		fuelType    fuel type of output
		minLNG      minimum liquid natural gas output

	"""

	def __init__(self):
		"""
		This class creates an instance of the GenC class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.refName = None
		self.refClass = None
		self.refNum = None
		self.maxOil = None
		self.minOil = None
		self.fuelType = None
		self.status = None
		self.controller = []


	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the Refinery object with functionality.
		"""

		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'process crude oil'), ('operand','crude oil'),('output', 'processed oil'), ('status',self.status), ('weightIn','1.285')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the Refinery object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
			 ('name', 'process crude oil'), ('operand', 'crude oil'), ('output', 'processed oil'),
			 ('status', self.status),('controller',', '.join(self.controller)), ('weightIn','1.285')]))
		resourceCount[0] += 1
		resourceIdx[self.nodeName] = resource
		return resourceCount, resourceIdx