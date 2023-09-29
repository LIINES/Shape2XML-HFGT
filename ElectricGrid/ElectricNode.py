#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""
import xml.etree.ElementTree as ET
from collections import OrderedDict

class ElectricNode(object):
	def __init__(self):
		"""
		This function initializes the electric node attributes.
		:return: Empty electric node object
		"""
		self.nodeName = None
		self.nodeNum = None
		self.nodeType = None
		self.status = None
		self.gpsX = None
		self.gpsY = None
		self.busArea = None
		self.busNum = None
		self.pInject = None
		self.qInject = None
		self.type = 'buffer'
		self.cluster = None


	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def __getNum__(self):
		return self.nodeNum

	def __getName__(self):
		return self.nodeName

	def get_coordinate(self):
		return [self.gpsX, self.gpsY]

	def get_status(self):
		return self.status

	def initialize_electric_node(self, data):
		"""
		This function creates an instance of ElecNode from a dictionary.
		:param data: a dictionary containing data for the instance.
		:return: an instantiated ElecNode object.
		"""
		attribs = self.__dict__.keys()
		for key, value in data.items():
			if key in attribs:
				setattr(self, key, value)
		return self

	def add_xml_child_hfgt(self,parent):
		"""
		This creates an XML branch for the Node object with example functionality.
		"""
		machine = ET.SubElement(parent, 'Machine', OrderedDict(
			[('name', self.nodeName), ('gpsX', str(self.gpsX)),('gpsY', str(self.gpsY)),('controller',', '.join(self.controller))]))
		method_form = ET.SubElement(machine, 'MethodxForm', OrderedDict(
			[('name', 'transform 1'), ('operand', 'input 1'), ('output', 'output 1'),('status', 'true')]))
		method_port = ET.SubElement(machine, 'MethodxPort', OrderedDict(
			[('name', 'store 1'), ('operand', 'input 1'), ('output', 'output 1'),
			 ('origin', self.nodeName), ('dest', self.nodeName), ('ref', 'operand 1'),('status', 'true')]))

	def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
		"""
		This creates an XML branch for the Node object with example functionality.
		"""
		resource = resourceCount[0]
		method_form = ET.SubElement(parent, 'MethodxForm', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)),('gpsY', str(self.gpsY)), ('name', 'transform 1'), ('operand', 'input 1'), ('output', 'output 1'), ('status', 'true'), ('controller',', '.join(self.controller))]))
		method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict(
			[('resource', str(resource)), ('gpsX', str(self.gpsX)),('gpsY', str(self.gpsY)), ('name', 'store 1'), ('operand', 'input 1'), ('output', 'output 1'),
			 ('origin', str(resource)), ('dest', str(resource)), ('ref', 'operand 1'), ('status', 'true'),('controller',', '.join(self.controller))]))

		resourceCount[0] += 1
		resourceIdx[self.nodeName] = resource
		return resourceCount, resourceIdx

