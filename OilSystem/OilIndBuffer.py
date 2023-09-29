#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

from ElectricGrid.ElectricNode import ElectricNode
# from lxml import etree as ET
import xml.etree.ElementTree as ET
from collections import OrderedDict


class OilIndBuffer(ElectricNode):
	"""
	This class represents NG system independent buffers.
	Attributes:
		busNum:			bus number (positive integer)
		busType: 		bus type
		status:			bus status (1 = in-service, 0 = out-of-service)
		nodeType:		prints the classname
		attrib_Ref:		node refinements
	"""
	def __init__(self):
		"""
		Construct a new bus with all parameters set to nonetype
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.busNum = None
		self.busName = None
		self.busType = None
		self.attrib_ref = None
		self.status = None
		self.controller = []


	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the independent buffer object with functionality.
		"""

		indBuffer = ET.SubElement(parent, 'IndBuffer', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)) ,('controller',', '.join(self.controller))]))
		for k1 in self.attrib_ref:
			method_port = ET.SubElement(indBuffer, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', k1), ('output', k1), ('origin', self.nodeName), ('dest', self.nodeName), ('ref', k1),('status','true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the independent buffer object with functionality.
		"""
		resource = resourceCount[1]
		for k1 in self.attrib_ref:
			method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
				[('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', k1), ('output', k1), ('origin', "indBuff'"+str(resource)+"'"),
				 ('dest', "indBuff'"+str(resource)+"'"), ('ref', k1), ('status', 'true'),('controller',', '.join(self.controller))]))

		resourceCount[1] += 1
		resourceIdx[self.nodeName] = "indBuff'"+str(resource)+"'"
		return resourceCount, resourceIdx