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


class Compressor(ElectricNode):
	"""
	This class represents all NG system compressors.

	Attributes:
		compNum     	compressor number (positive integer)
		nodeName    	node name
		compName    	compressor name
		compClass   	compressor class
		maxFlow     	maximum flow gas output
		minFlow     	minimum flow gas output
		maxPressure     maximum gas pressure
		minPressure     minimum gas pressure
		fuelType     	compressor fuel type
		status      	machine status, >0 = machine in-service, 0 = machine out-of-service
	"""

	def __init__(self):
		"""
		This class creates an instance of the Compressor class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.compNum = None
		self.nodeName = None
		self.compName = None
		self.compClass = None
		self.maxFlow = None
		self.minFlow = None
		self.maxPressure = None
		self.minPressure = None
		self.fuelType = None
		self.status = None
		self.controller = []


	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the compressor object with functionality.
		"""

		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'compress processed gas'), ('operand','processed gas'),('output', 'processed gas'), ('status', self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'compress syngas'), ('operand','syngas'),('output', 'syngas'), ('status',self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'compress raw gas'), ('operand','raw gas'),('output', 'raw gas'), ('status',self.status)]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the compressor object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict([('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'compress processed gas'), ('operand', 'processed gas'), ('output', 'processed gas'),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'compress syngas'), ('operand', 'syngas'), ('output', 'syngas'), ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'compress raw gas'), ('operand', 'raw gas'), ('output', 'raw gas'), ('status', self.status),('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.nodeName] = resource
		return resourceCount, resourceIdx