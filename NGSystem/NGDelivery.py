"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

from ElectricGrid.ElectricNode import ElectricNode
import xml.etree.ElementTree as ET
from collections import OrderedDict

class NGDelivery(ElectricNode):
	"""
	This class represents all NG Receipt and Delivery.

	Attributes:
		RDNum       RD number (positive integer)
		nodeName    node name
		RDName		RD name
		procClass   processor class
		maxFlow     maximum natural gas output
		minFlow     minimum natural gas output
		fuelType	fuel type handled
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
	"""
	def __init__(self):
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.RDNum = None
		self.nodeName = 'NGDelivery'
		self.RDName = None
		self.maxFlow = None
		self.minFlow = None
		self.fuelType = None
		self.status = None
		self.controller = []


	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the Receipt Delivery object with functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.RDName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import processed gas'), ('operand',''),('output', 'processed gas'), ('status',self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import syngas'), ('operand',''),('output', 'syngas'), ('status',self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import raw gas'), ('operand',''),('output', 'raw gas'), ('status',self.status)]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'export processed gas'), ('operand','processed gas'),('output', ''), ('status',self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'processed gas'), ('output', 'processed gas'),('origin', self.RDName), ('dest', self.RDName), ('ref', 'processed gas'),('status', self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'syngas'), ('output', 'syngas'),('origin', self.RDName), ('dest', self.RDName), ('ref', 'syngas'),('status', self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'raw gas'), ('output', 'raw gas'),('origin', self.RDName), ('dest', self.RDName), ('ref', 'raw gas'),('status', self.status)]))

	def add_xml_child_hfgt_dofs(self,parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the Receipt Delivery object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'import processed gas'), ('operand', ''), ('output', 'processed gas'),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'import syngas'), ('operand', ''), ('output', 'syngas'), ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'import raw gas'), ('operand', ''), ('output', 'raw gas'), ('status', self.status),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'export processed gas'), ('operand', 'processed gas'), ('output', ''),
			 ('status', self.status),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'processed gas'), ('output', 'processed gas'), ('origin', str(resource)),
			 ('dest', str(resource)), ('ref', 'processed gas'), ('status', self.status),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'syngas'), ('output', 'syngas'), ('origin', str(resource)),
			 ('dest', str(resource)), ('ref', 'syngas'), ('status', self.status),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'raw gas'), ('output', 'raw gas'), ('origin', str(resource)),
			 ('dest', str(resource)), ('ref', 'raw gas'), ('status', self.status),('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.RDName] = resource
		return resourceCount, resourceIdx