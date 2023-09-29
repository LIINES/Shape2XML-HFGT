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

class LoadS(ElectricNode):
	"""
	This class represents all power systems stochastic loads' cyber agents.

	Attributes:
		loadSNum:       the number of the LoadS
		peakLoadS:      the peak MW value
		maxP:           maximum power
		minP:           minimum power
		profileRT:      real-time power profile
		profileErr:     real-time forecast error
		err:            percent error
		capacity:       MW installed capacity
		linearC:          linear cost for demand response
		maxQ:           maximum reactive power
		minQ:           minimum reactive power
		rNode:
		xNode
		nodeType:

	"""

	def __init__(self):
		"""
		This function instantiates the loadS agent with all attributes set to None type or default value.
		"""
		PowerNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.loadSNum = None
		self.peakLoadS = None
		self.maxP = None
		self.minP = None
		self.maxQ = None
		self.minQ = None
		self.rNode = None
		self.xNode = None
		self.profileRT = None
		self.profileErr = None
		self.err = None
		self.capacity = None
		self.linearC = None
		self.curtail = None
		self.currentCurtail = None
		self.forecast = None
		self.controller = []

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the LoadS object with functionality.
		"""

		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.loadName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'consume electric power'), ('operand', 'electric power at 132kV'), ('output', ''),('status','true')]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', self.loadName), ('dest', self.loadName), ('ref', 'electric power at 132kV'),('status','true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the LoadS object with functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
			 ('name', 'consume electric power'), ('operand', 'electric power at 132kV'), ('output', ''),
			 ('status', 'true'), ('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
			 ('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'electric power at 132kV'),
			 ('status', 'true'), ('controller',', '.join(self.controller))]))
		resourceCount[0] += 1
		resourceIdx[self.loadName] = resource
		return resourceCount, resourceIdx