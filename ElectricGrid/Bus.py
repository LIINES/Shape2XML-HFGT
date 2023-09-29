#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

import math as mt
from ElectricGrid.ElectricNode import ElectricNode
import xml.etree.ElementTree as ET
from collections import OrderedDict


class Bus(ElectricNode):
	"""
	This class represents all power system buses.
	Attributes:
		busNum:			bus number (positive integer)
		busType: 		bus type (RS = reference, LS = load, GS = generation)
		status:			bus status (1 = in-service, 0 = out-of-service)
		pDemand:		real power demand (MW)
		qDemand:		reactive power demand (MVAr)
		gShunt:			shunt conductance (MW demanded at V = 1.0 p.u.)
		bShunt: 		shunt susceptance (MVAr injected at V = 1.0 p.u.)
		busArea:		area number (positive integer)
		voltageMag:		voltage magnitude (p.u.)
		voltageAng:		voltage angle (degrees)
		lossZone:		loss zone (positive integer)
		maxV:			maximum voltage magnitude (p.u.)
		minV:			minimum voltage magnitude (p.u.)
		nodeType:		prints the classname
		attrib_Ref:		node refinements
	"""
	def __init__(self):
		"""
		This class creates an instance of the Bus class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.busNum = None
		self.busName = None
		self.busType = None
		self.status = None
		self.pDemand = None
		self.qDemand = None
		self.gShunt = None
		self.bShunt = None
		self.busArea = None
		self.voltageMag = None
		self.voltageAng = None
		self.maxA = mt.pi/2
		self.minA = -mt.pi/2
		self.baseKV = None
		self.lossZone = None
		self.maxV = None
		self.minV = None
		self.attrib_ref = None
		self.controller = []


	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the ElectricLine object with functionality.
		"""

		indBuffer = ET.SubElement(parent, 'IndBuffer', OrderedDict([('name', self.nodeName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		for k1 in self.attrib_ref:
			method_port = ET.SubElement(indBuffer, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', k1), ('output', k1), ('origin', self.nodeName), ('dest', self.nodeName), ('ref', k1), ('status', 'true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the ElectricLine object with functionality.
		"""
		resource = resourceCount[1]
		for k1 in self.attrib_ref:
			method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
				[('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', k1), ('output', k1), ('origin', "indBuff'"+str(resource)+"'"),
				 ('dest', "indBuff'"+str(resource)+"'"), ('ref', k1), ('status', 'true'),('controller',', '.join(self.controller))]))

		resourceCount[1] += 1
		resourceIdx[self.nodeName] = "indBuff'"+str(resource)+"'"
		return resourceCount, resourceIdx