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

class GenC(ElectricNode):
	"""
	This class represents all power systems controllable generators.

	Attributes:
		busNum      bus number (positive integer)
		genName     generator name
		genClass    generator class
		status      machine status, >0 = machine in-service, 0 = machine out-of-service
		status1     machine status at the previous security-constrained economic dispatch (SCED)
		status2     machine status at the next SCED
		maxP        maximum real power output (MW)
		minP        minimum real power output (MW)
		maxQ        maximum reactive power output (MVAr)
		minQ        minimum reactive power output (MVAr)
		maxR        maximum real power ramp rate (MW/min)
		minR        minimum real power ramp rate (MW/min)
		upTime      the current up time. Attribute initialized to 14400
		dnTime      the current down time. Attribute initialized to 14400
		startUps    the current number of start-ups. Attribute initialized to 0

		minUpTime       minimum time the generator should be on before shutting down
		minDownTime     minimum time the generator should be off before starting up
		maxStartUps     maximum number of start-ups in the day
		vMag            voltage magnitude set point (p.u.)
	"""

	def __init__(self):
		"""
		This class creates an instance of the GenC class with each attribute set to none type.
		"""
		ElectricNode.__init__(self)
		self.genCType = None
		self.nodeType = self.__class__.__name__
		self.genName = None
		self.genClass = None
		self.genCNum = None
		self.mBase = 100
		self.upTime = 14400
		self.dnTime = 14400
		self.maxP = None
		self.minP = None
		self.maxQ = None
		self.minQ = None
		self.maxR = None
		self.minR = None
		self.vMag = None
		self.rNode = None
		self.xNode = None
		self.fuelType = None
		self.startUpH = None
		self.shutDnH = None
		self.fixedH = None
		self.linearH = None
		self.quadH = None
		self.startUpC = None
		self.shutDnC = None
		self.fixedC = None
		self.linearC = None
		self.quadC = None
		self.status = None
		self.status1 = None
		self.status2 = None
		self.startUps = 0
		self.minUpTime = None
		self.minDownTime = None
		self.maxStartUps = None
		self.controller = []

	def add_xml_child_hfgt(self, parent):
		"""
		This creates an XML branch for the GenC object with functions based on the objects fuel type.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict([('name', self.genName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
		for k1 in range(len(self.fuelType)):
			fuel = self.fuelType[k1]
			if fuel == '':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power'), ('operand',''),('output', 'electric power at 132kV'), ('status','true'), ('cap', str(self.cap[k1]))]))
			elif fuel == 'processed gas':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from processed gas'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status','true'), ('cap', str(self.cap[k1])), ('weightIn', '2.253')]))
			elif fuel == 'processed oil':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from processed oil'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status','true'), ('cap', str(self.cap[k1])), ('weightIn', '3.289')]))
			elif fuel == 'syngas':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from syngas'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('weightIn', '2.253')]))
			elif fuel == 'coal':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from coal'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('weightIn', '3.102')])) #10853 btu->11.166 MJ->0.011166 GJ for 0.0036GJ
			elif fuel == 'uranium':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from uranium'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('weightIn', '3.056')]))
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'import uranium'), ('operand',''), ('output', fuel), ('status', 'true')]))
			elif fuel == 'solid biomass feedstock':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from solid biomass feedstock'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('weightIn', '3')]))
			elif fuel == 'liquid biomass feedstock':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from liquid biomass feedstock'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('weightIn', '3')]))
			elif fuel == 'water energy':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from water energy'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict(
					[('name', 'import water energy'), ('operand',''), ('output', fuel), ('status', 'true')]))
			elif fuel == 'solar':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from solar'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict(
					[('name', 'import solar'), ('operand',''), ('output', fuel), ('status', 'true')]))
			elif fuel == 'wind energy':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from wind energy'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict(
					[('name', 'import wind energy'), ('operand',''), ('output', fuel), ('status', 'true')]))
			elif fuel == 'other':
				method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict([('name', 'generate electric power from other'), ('operand', fuel), ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1]))]))
			else:
				print('unhandled generation fuel source please create handling')
				print(fuel)
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', self.genName), ('dest', self.genName), ('ref', 'electric power at 132kV'),('status', 'true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the GenC object with functions based on the objects fuel type.
		"""
		resource = resourceCount[0]
		for k1 in range(len(self.fuelType)):
			fuel = self.fuelType[k1]
			if fuel == '':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power'), ('operand', ''), ('output', 'electric power at 132kV'),
					 ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller))]))
			elif fuel == 'processed gas':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from processed gas'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '2.253')]))
			elif fuel == 'processed oil':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from processed oil'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '3.289')]))
			elif fuel == 'syngas':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from syngas'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '2.253')]))
			elif fuel == 'coal':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from coal'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '3.102')]))
			elif fuel == 'uranium':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from uranium'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '3.056')]))
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)),
					 ('name', 'import uranium'), ('operand', ''),
					 ('output', fuel), ('status', 'true'),
					 ('controller', ', '.join(self.controller))]))
			elif fuel == 'solid biomass feedstock':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from solid biomass feedstock'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '3')]))
			elif fuel == 'liquid biomass feedstock':
				method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
					[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'generate electric power from liquid biomass feedstock'), ('operand', fuel),
					 ('output', 'electric power at 132kV'), ('status', 'true'), ('cap', str(self.cap[k1])), ('controller',', '.join(self.controller)), ('weightIn', '3')]))
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
				print('unhandled generation fuel source please create handling')
				print(fuel)
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'electric power at 132kV'),
			 ('status', 'true'), ('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.genName] = resource
		return resourceCount, resourceIdx