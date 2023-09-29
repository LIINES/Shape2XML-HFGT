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

class GenS(ElectricNode):
	"""
	This class represents all power systems stochastic generators.

	Attributes:
		busNum      bus number (positive integer)
		genName     generator name
		genClass    generator class
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
		maxP        maximum real power output (MW)
		minP        minimum real power output (MW)
		maxQ        maximum reactive power output (MVAr)
		minQ        minimum reactive power output (MVAr)
		maxR        maximum real power ramp rate (MW/min)
		minR        minimum real power ramp rate (MW/min)
		err         % forecast error
		profileRT   the real-time profile
		profileErr  the error profiles for variable energy resource (VER)
		genSType    the type of VER could be wind, solar PV, run-of-river hydro
		capacity    capacity profiles for the VER
		curtail     curtailable percentage
	"""

	def __init__(self):
		"""
		This function creates an instance of a class with attributes initialized to none type.
		"""
		ElectricNode.__init__(self)
		self.nodeType = self.__class__.__name__
		self.genName = None
		self.genSType = None
		self.status = None
		self.capacity = None
		self.curtail = None
		self.currentCurtail = None
		self.maxR = None
		self.minR = None
		self.maxQ = None
		self.minQ = None
		self.maxP = None
		self.minP = None
		self.profileRT = None
		self.profileErr = None
		self.err = None
		self.rNode = None
		self.xNode = None
		self.capacity = None
		self.err = None
		self.variability = None
		self.linearC = None
		self.forecast = None
		self.fuelType = None
		self.controller = []

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the GenS object with functions based on the objects fuel type.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.genName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
		for k1 in range(len(self.fuelType)):
			fuel = self.fuelType[k1]
			if fuel == '':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power'), ('operand',''),('output', 'electric power at 132kV'), ('status','true'), ('cap', str(self.cap[k1]))]))
			elif fuel == 'water energy':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from water energy'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
			elif fuel == 'solar':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from solar'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
			elif fuel == 'wind energy':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from wind energy'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
			elif fuel == 'other':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from other'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
			else:
				print('unhandled generation fuel source')
				print(fuel)

		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),('origin', self.genName), ('dest', self.genName), ('ref', 'electric power at 132kV'),('status', 'true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the GenS object with functions based on the objects fuel type.
		"""
		resource = resourceCount[0]
		for k1 in range(len(self.fuelType)):
			fuel = self.fuelType[k1]
		if fuel == '':
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power'), ('operand', ''), ('output', 'electric power at 132kV'),
				 ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller))]))
		elif fuel == 'water energy':
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from water energy'), ('operand', fuel),
				 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller))]))
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
				 ('name', 'import water energy'), ('operand', ''),
				 ('output', fuel), ('status', 'true'),
				 ('controller', ', '.join(self.controller))]))
		elif fuel == 'solar':
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from solar'), ('operand', fuel),
				 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller))]))
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
				 ('name', 'import solar'), ('operand', ''),
				 ('output', fuel), ('status', 'true'),
				 ('controller', ', '.join(self.controller))]))
		elif fuel == 'wind energy':
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from wind energy'), ('operand', fuel),
				 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller))]))
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
				 ('name', 'import wind energy'), ('operand', ''),
				 ('output', fuel), ('status', 'true'),
				 ('controller', ', '.join(self.controller))]))
		elif fuel == 'other':
			method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
				[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from other'), ('operand', fuel),
				 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller))]))
		else:
			print('unhandled generation fuel source')
			print(fuel)

		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'electric power at 132kV'),
			 ('status', 'true'), ('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.genName] = resource
		return resourceCount, resourceIdx