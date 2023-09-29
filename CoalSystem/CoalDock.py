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

class CoalDock(ElectricNode):
	"""
	This class represents all coal systems controllable Docks.

	Attributes:
		dockNum     dock number (positive integer)
		nodeName    Node name
		dockName   	Dock name
		dockClass   dock class
		maxCoal     maximum coal output
		minCoal     minimum coal output
		fuelType    fuel source dealt with
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
		cluster		Cluster node belongs too
	"""

	def __init__(self):
		"""
		This class creates an instance of the Dock class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.dockNum = None
		self.nodeName = None
		self.dockName = None
		self.dockClass = None
		self.maxCoal = None
		self.minCoal = None
		self.status = None
		self.cluster = None
		self.controller = []


	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the dock object with functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import coal'), ('operand',''),('output', 'coal'), ('status',self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'export coal'), ('operand','coal'),('output', ''), ('status',self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'coal'), ('output', 'coal'),('origin', self.nodeName), ('dest', self.nodeName), ('ref', 'coal'),('status', self.status)]))

	def add_xml_child_hfgt_dofs(self,parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the dock object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'import coal'), ('operand', ''), ('output', 'coal'), ('status', self.status), ('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'export coal'), ('operand', 'coal'), ('output', ''), ('status', self.status), ('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'coal'), ('output', 'coal'), ('origin', str(resource)),
			 ('dest', str(resource)), ('ref', 'coal'), ('status', self.status), ('controller',', '.join(self.controller))]))
		resourceCount[0] += 1
		resourceIdx[self.nodeName] = resource
		return resourceCount, resourceIdx