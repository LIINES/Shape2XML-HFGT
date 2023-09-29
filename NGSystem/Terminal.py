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


class Terminal(ElectricNode):
	"""
	This class represents all NG systems Terminals.

	Attributes:
		termNum     terminal number (positive integer)
		nodeName    node name
		termName    terminal name
		termClass   terminal class
		maxNG       maximum real natural gas output
		minNG       minimum real natural gas output
		maxLNG      maximum liquid natural gas output
		minLNG      minimum liquid natural gas output
		fuelType	fuel type the terminal works with
		status      machine status, >0 = machine in-service, 0 = machine out-of-service


	"""

	def __init__(self):
		"""
		This class creates an instance of the GenC class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.termNum = None
		self.nodeName = None
		self.termName = None
		self.termClass = None
		self.maxNG = None
		self.minNG = None
		self.maxLNG = None
		self.minLNG = None
		self.fuelType = None
		self.status = None
		self.controller = []

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the terminal object with functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import processed gas'), ('operand',''),('output', 'processed gas'), ('status',self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'export processed gas'), ('operand','processed gas'),('output', ''), ('status',self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'processed gas'), ('output', 'processed gas'),('origin', self.nodeName), ('dest', self.nodeName), ('ref', 'processed gas'),('status', self.status)]))

		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict(
			[('name', 'import raw gas'), ('operand', ''), ('output', 'raw gas'), ('status', self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict(
			[('name', 'export raw gas'), ('operand', 'raw gas'), ('output', ''), ('status', self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict(
			[('name', 'store'), ('operand', 'raw gas'), ('output', 'raw gas'), ('origin', self.nodeName),
			 ('dest', self.nodeName), ('ref', 'raw gas'), ('status', self.status)]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the terminal object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'import processed gas'), ('operand', ''), ('output', 'processed gas'),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'export processed gas'), ('operand', 'processed gas'), ('output', ''),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'processed gas'), ('output', 'processed gas'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'processed gas'),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
			 ('name', 'import raw gas'), ('operand', ''), ('output', 'raw gas'),
			 ('status', self.status), ('controller', ', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
			 ('name', 'export raw gas'), ('operand', 'raw gas'), ('output', ''),
			 ('status', self.status), ('controller', ', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'),
			 ('operand', 'raw gas'), ('output', 'raw gas'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'raw gas'),
			 ('status', self.status), ('controller', ', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.nodeName] = resource
		return resourceCount, resourceIdx
