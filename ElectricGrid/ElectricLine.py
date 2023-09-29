#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

import numpy as np
import xml.etree.ElementTree as ET
from collections import OrderedDict

class ElectricLine(object):
	"""
		This class represents all power systems electric lines.

		Attributes:
			fBus 		from bus number
			tBus 		to bus number
			rLine 		resistance (p.u.)
			xLine 		reactance (p.u.)
			bLine 		total line charging susceptance (p.u.)
			rateA 		MVA rating A (long term rating)
			rateB 		MVA rating B (short term rating)
			rateC 		MVA rating C (emergency rating)
			tap 		transformer off nominal turns ratio, (taps at 'from' bus, impedance at 'to'
						bus, i.e. if r = x = 0, tap = |Vf|/|Vt|)
			ang 		transformer phase shift angle (degrees), positive => delay
			status 		initial line status, 1 = in-service, 0 = out-of-service
			angMin 		minimum angle difference, ?f??t (degrees)
			angMax 		maximum angle difference, ?f??t (degrees)
			pf 			real power injected at ?from? bus end (MW)
			qf 			reactive power injected at ?from? bus end (MVAr)
			pt  		real power injected at ?to? bus end (MW)
			qt  		reactive power injected at ?to? bus end (MVAr)
			refinement	HFGT function refinement
			lineName	name given to the line
		"""

	def __init__(self):
		"""
		This class creates an instance of the ElectricLine class with each attribute set to none type.
		"""

		self.fBus = None
		self.tBus = None
		self.rLine = None
		self.xLine = None
		self.bLine = None
		self.rateA = None
		self.rateB = None
		self.rateC = None
		self.tap = None
		self.ang = None
		self.status = None
		self.angMin = None
		self.angMax = None
		self.status = None
		self.pf = None
		self.qf = None
		self.pt = None
		self.qt = None
		self.maxP = None
		self.minP = None
		self.minQ = None
		self.maxQ = None
		self.lineName = None
		self.refinement = None
		self.type = 'ElecLine'
		self.controller = []


	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)


	def get_status(self):
		return self.status

	def get_origin(self):
		return self.fBus

	def get_dest(self):
		return self.tBus

	def get_rline(self):
		return self.rLine

	def initialize_electric_line(self, data):
		for key, value in data.items():
			setattr(self, key, value)
		return self

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the ElectricLine object with functionality.
		"""
		transporter = ET.SubElement(parent, 'Transporter', OrderedDict([('name', self.lineName), ('controller',', '.join(self.controller))]))
		# add transportation capabilities in both directions
		for k1 in self.refinement:
			method_port1 = ET.SubElement(transporter, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('status', 'true'), ('origin', self.fBus), ('dest', self.tBus),
				 ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('ref', k1)]))
			method_port2 = ET.SubElement(transporter, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('status', 'true'), ('origin', self.tBus), ('dest', self.fBus),
				 ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('ref', k1)]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the ElectricLine object with functionality.
		"""
		resource = sum(resourceCount)
		for k1 in self.refinement:
			method_port1 = ET.SubElement(parent, 'MethodxPort', OrderedDict(
				[('resource', str(resource)), ('name', 'transport'), ('status', 'true'), ('origin', str(resourceIdx[self.fBus])), ('dest', str(resourceIdx[self.tBus])),
				 ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),
				 ('ref', k1), ('controller',', '.join(self.controller))]))
			method_port2 = ET.SubElement(parent, 'MethodxPort', OrderedDict(
				[('resource', str(resource)), ('name', 'transport'), ('status', 'true'), ('origin', str(resourceIdx[self.tBus])), ('dest', str(resourceIdx[self.fBus])),
				 ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),
				 ('ref', k1), ('controller',', '.join(self.controller))]))
		resourceCount[2] += 1
		return resourceCount