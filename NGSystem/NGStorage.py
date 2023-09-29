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

class NGStorage(ElectricNode):
	"""
	This class represents all NG storage facilities.

	Attributes:
		storeNum    storage number (positive integer)
		storeName   storage name
		nodeName	node name
		storeClass  storage class
		maxNG       maximum real natural gas output
		minNG       minimum real natural gas output
		fuelType	storage fuel type
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
	"""

	def __init__(self):
		"""
		This class creates an instance of the NGStorage class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.storeNum = None
		self.storeName = None
		self.nodeName = None
		self.storeClass = None
		self.maxNG = None
		self.minNG = None
		self.fuelType = None
		self.status = None
		self.region = None
		self.controller = []

	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the storage object with functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.storeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'processed gas'), ('output', 'processed gas'),('origin', self.storeName), ('dest', self.storeName), ('ref', 'processed gas'),('status', self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'syngas'), ('output', 'syngas'),('origin', self.storeName), ('dest', self.storeName), ('ref', 'syngas'),('status', self.status)]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'raw gas'), ('output', 'raw gas'),('origin', self.storeName), ('dest', self.storeName), ('ref', 'raw gas'),('status', self.status)]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the storage object with functionality.
		"""
		resource = resourceCount[1]
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict([('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'processed gas'), ('output', 'processed gas'),('origin', "indBuff'"+str(resource)+"'"), ('dest', "indBuff'"+str(resource)+"'"), ('ref', 'processed gas'),('status', self.status),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict([('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'syngas'), ('output', 'syngas'),('origin', "indBuff'"+str(resource)+"'"), ('dest', "indBuff'"+str(resource)+"'"), ('ref', 'syngas'),('status', self.status),('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict([('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'raw gas'), ('output', 'raw gas'),('origin', "indBuff'"+str(resource)+"'"), ('dest', "indBuff'"+str(resource)+"'"), ('ref', 'raw gas'),('status', self.status),('controller',', '.join(self.controller))]))

		resourceCount[1] += 1
		resourceIdx[self.storeName] = "indBuff'"+str(resource)+"'"
		return resourceCount, resourceIdx