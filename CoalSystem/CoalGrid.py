#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""
import numpy as np
import geopandas as gpd
import scipy.sparse as sp
from lxml import etree as ET
from collections import OrderedDict

from ElectricGrid.GenC import GenC
from CoalSystem.CoalDock import CoalDock
from CoalSystem.CoalRailroad import CoalRailroad
from CoalSystem.CoalSource import CoalSource
from CoalSystem.CoalIndBuffer import CoalIndBuffer

class CoalGrid:
	"""
	This class represents the physical coal system which contains coal power plants, docks, railroads, and sources.

	Attributes:
		 genC        		Coal PowerPlants
		 CoalDock   		Coal docks
		 CoalSource      	Coal sources
		 CoalIndBuffer      coal independent buffers
		 CoalRailroad       coal railroads
		 buffer_map       	coal buffer maps of gps coords
		 refinements   		refinements in coal system
	"""

	def __init__(self):
		"""
		This function initializes all of the CoalGrid attributes.
		:return: Empty CoalGrid object
		"""
		self.name = self.__class__.__name__
		self.genC = []
		self.CoalDock = []
		self.CoalSource = []
		self.CoalIndBuffer = []
		self.CoalRailroad = []
		self.buffer_map = {}
		self.refinements = ['coal']

	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def initialize_Coal_system(self, datafiles):
		"""
		Instantiate the CoalGrid by reading all the individual resource files. The
		coal power plant, docks, sources, independent buffer, and Railroads.

		:param datafiles: List of shape files to read in
		:return:
		"""
		print('Instantiating Coal System')

		self.instantiate_CoalPowerPlant(datafiles)

		self.instantiate_CoalDock(datafiles)

		self.instantiate_CoalSource(datafiles)

		self.instantiate_CoalRailroad(datafiles)

		return self

	def instantiate_CoalPowerPlant(self, data):
		"""
		This function takes an input data list and instantiates all the genC.
		:param data: a list of all data files
		:return: CoalGrid updated with all the genC
		"""
		print('Instantiating Coal Power Plants')

		fuels = set()
		plant_count = 0
		skipped_power_plants = 0
		for file in data:
			if 'PowerPlant' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('PowerPlant file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]
				df = df[df['STATUS']!='NOT_OP']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				for index,instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_power_plants += 1
						continue

					plant_count += 1
					new_instance = GenC()
					new_instance.nodeName = 'Coal Power Plant ' + str(plant_count)
					new_instance.genName = 'Coal Power Plant ' + str(plant_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.cap = [max([instance['OP_CAP'], instance['SUMMER_CAP'], instance['WINTER_CAP']])]
					new_instance.fuelType = instance['FUEL_CAT']
					new_instance, fuels = self.set_fuel(new_instance, fuels)
					new_instance.refinement = ['electric power at 132kV']+ new_instance.fuelType
					for k1 in new_instance.refinement:
						if k1 not in self.refinements:
							self.refinements.append(k1)
					new_instance.status = 'true'
					new_instance.type = 'buffer'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in  coal .SHP file')
					try:
						new_instance.iso = instance['ISO']
					except:
						print('No ISO attribute in coal .SHP file')
					self.genC.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.genName

				skipped_power_plants = skipped_power_plants + init_plants-df.shape[0]

		return self

	def instantiate_CoalDock(self, data):
		"""
		This function takes as input data list and instantiates all the docks.
		:param data: a list of all data files
		:return: CoalGrid updated with all the docks
		"""
		print('Instantiating Coal Docks')

		CoalDock_map = {}
		CoalDock_count = 0
		skipped_CoalDock = 0
		for file in data:
			if 'Dock' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Dock file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_CoalDock += 1
						continue

					CoalDock_count += 1
					new_instance = CoalDock()
					new_instance.nodeName = 'Coal Dock ' + str(CoalDock_count)
					new_instance.dockName = 'Coal Dock ' + str(CoalDock_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.type = 'buffer'
					new_instance.refinement = ['coal']
					for k1 in new_instance.refinement:
						if k1 not in self.refinements:
							self.refinements.append(k1)
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.CoalDock.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.dockName

		return self

	def instantiate_CoalSource(self, data):
		"""
		This function takes as input data list and instantiates all the sources.
		:param data: a list of all data files
		:return: CoalGrid updated with all the sources
		"""
		print('Instantiating Coal Sources')

		CoalSource_map = {}
		CoalSource_count = 0
		skipped_CoalSource = 0
		for file in data:
			if 'Source' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Source file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]
				df = df[df['STATUS']!='Closed']
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				for index,instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_CoalSource += 1
						continue

					CoalSource_count += 1
					new_instance = CoalSource()
					new_instance.nodeName = 'Coal Source ' + str(CoalSource_count)
					new_instance.sourceName = 'Coal Source ' + str(CoalSource_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.status = 'true'
					new_instance.type = 'buffer'
					new_instance.refinement = ['coal']
					for k1 in new_instance.refinement:
						if k1 not in self.refinements:
							self.refinements.append(k1)
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.CoalSource.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.sourceName

		return self

	def instantiate_CoalRailroad(self, data):
		"""
		This function takes as input data list and instantiates all the railroads.
		:param data: a list of all data files
		:return: CoalGrid updated with all the railroads
		"""
		print('Instantiating Coal Railroads')

		for file in data:
			if 'Railroad' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Railroad file doesnt exist: ' + file)
					continue
				CoalRailroad_count = 0
				skipped_CoalRailroad = 0
				init_CoalRailroad = df.shape[0]

				for index, instance in df.iterrows():
					coords = [(round(pnt.x,4),round(pnt.y,4)) for pnt in instance.geometry.boundary]
					if len(coords)<2:
						skipped_CoalRailroad += 1
						continue

					CoalRailroad_count += 1
					new_instance = CoalRailroad()
					lineOrigin = coords[0]
					lineDest = coords[-1]
					new_instance.fBus = lineOrigin
					new_instance.tBus = lineDest
					new_instance.lineName = 'Coal Railroad ' + str(CoalRailroad_count)
					new_instance.refinement = ['coal']
					new_instance.fuelType = ['coal']
					for k1 in new_instance.refinement:
						if k1 not in self.refinements:
							self.refinements.append(k1)
					new_instance.status = 'true'
					self.CoalRailroad.append(new_instance)

		skipped_CoalRailroad = skipped_CoalRailroad + init_CoalRailroad - df.shape[0]
		return self

	def set_fuel(self, node, fuels):
		"""
		This function takes as input node and set of fuels.
		:param node: node object
		:param fuels: set of fuels
		:return: node with updated fuel source and updated fuel set with unhandled fuels.
		"""
		if node.fuelType in (
		'BUTANE', 'METHANOL', 'COAL BED METHANE', 'METHANE', 'LANDFILL GAS', 'Natural Gas', 'REFINERY GAS',
		'Processed Gas', 'GAS (GENERIC)', 'NATURAL GAS', 'HYDROGEN', 'BLAST FURNACE GAS',
		'COKE OVEN GAS', 'LIQUIFIED PROPANE GAS', 'Depleted Field', 'Salt Cavern', 'Aquifer', 'LNG',
							 'Hydrogen','Hydrogen Gas', 'Nitrogen','Other Gas', 'Empty Gas', 'Natural Gas Liquids'):
			node.fuelType = 'processed gas'
		elif node.fuelType in ('DISTILLATE OIL', 'NO. 1 FUEL OIL', 'NO. 6 FUEL OIL', 'KEROSENE', 'Oil', 'NO. 2 FUEL OIL',
							   'PETROLEUM COKE','DIESEL FUEL', 'COKE', 'HFO', 'NO. 5 FUEL OIL', 'RESIDUAL OILS', 'NO. 4 FUEL OIL',
							   'BLACK LIQUOR','REFUSED DERIVED FUEL','JET FUEL', 'FUEL OIL', 'Non-HVL Product','Non_HVL Products',
							   'Gasoline', 'Empty Liquid', 'Fuel Oil NO. 6', 'Fuel Oil', 'processed oil', 'Liquefied Petroleum Gas',
							   'Fuel Oil, Kerosene, Gasoline, Jet, Diesel', 'Fuel Grade Ethanol', 'Highly Volatile Liquid',
							   'Refined Products', 'Empty Hazardous Liquid or Gas', 'Unleaded Gasoline'):
			node.fuelType = 'processed oil'
		elif node.fuelType in ('CRUDE OIL', 'Crude Oil'):
			node.fuelType = 'crude oil'
		elif node.fuelType in ('LIGNITE COAL GAS (FROM COAL GASIFICATION)', 'WOOD GAS (FROM WOOD GASIFICATION)', 'ANTHRACITE',
							   'GAS FROM REFUSE GASIFICATION',
							   'GAS FROM BIOMASS GASIFICATION', 'COAL GAS (FROM COAL GASIFICATION)', 'GAS FROM FUEL OIL GASIFICATION',
							   'BITUMINOUS COAL GAS (FROM COAL GASIFICATION)'):
			node.fuelType = 'syngas'
		elif node.fuelType in (
		'WASTE COAL', 'GOB', 'COAL (GENERIC)', 'LIGNITE', 'Coal', 'SUBBITUMINOUS', 'BITUMINOUS COAL'):
			node.fuelType = 'coal'
		elif node.fuelType in ('URANIUM', 'Uranium'):
			node.fuelType = 'uranium'
		elif node.fuelType in ('AGRICULTURAL WASTE', 'REFUSE', 'MANURE', 'BIOMASS', 'TIRES', 'POULTRY LITTER'):
			node.fuelType = 'solid biomass feedstock'
		elif node.fuelType in (
		'WASTE WATER SLUDGE', 'DIGESTER GAS (SEWAGE SLUDGE GAS)', 'BIODIESEL', 'WASTE GAS', 'GEOTHERMAL STEAM',
		'WOOD WASTE LIQUIDS EXCL BLK LIQ (INCL RED LIQUOR,SLUDGE WOOD,SPENT SULFITE LIQUOR AND OTH LIQUIDS)'):
			node.fuelType = 'liquid biomass feedstock'
		elif node.fuelType in ('Water', 'Water Energy'):
			node.fuelType = 'water energy'
		elif node.fuelType in ('Solar'):
			node.fuelType = 'solar'
		elif node.fuelType in ('Wind'):
			node.fuelType = 'wind energy'
		elif node.fuelType in ('Other', 'WASTE HEAT', 'STEAM', 'UNKNOWN', 'COMPRESSED AIR', 'NOT APPLICABLE'):
			node.fuelType = 'other'
		else:
			print('Found a new fuel type that needs to be handled')
			print(node.fuelType)
			fuels.add(node.fuelType)

		if node.fuelType not in self.refinements:
			self.refinements.append(node.fuelType)

		node.fuelType = [node.fuelType]

		return node, fuels

	def getPtsGPSRef(self):
		"""
		retreive all the X and Y coordinates of all buffers and line endpoints

		:param self: takes its own Coal grid object as an input
		:return: ptsB_GPSX: matrix of buffer X coordinates of size buffers X refinements
		:return: ptsB_GPSY: matrix of buffer Y coordinates of size buffers X refinements
		:return: ptsOD_GPSX: matrix of line origin and destination X coordinates of size lines*2 X refinements
		:return: ptsOD_GPSY: matrix of line origin and destination Y coordinates of size lines*2 X refinements
		"""
		print('Entering getPtsGPSRef')
		ptsB = self.get_all_nodes()
		ptsOD_GPSX, ptsOD_GPSY = self.get_all_endpointsRef()

		ptsB_GPSX = sp.lil_matrix((len(ptsB), len(self.refinements)))
		ptsB_GPSY = sp.lil_matrix((len(ptsB), len(self.refinements)))
		for i, k1 in enumerate(ptsB):
			for k2 in k1.refinement:
				ptsB_GPSX[i, self.refinements.index(k2)] = k1.gpsX
				ptsB_GPSY[i, self.refinements.index(k2)] = k1.gpsY

		return ptsB_GPSX, ptsB_GPSY, ptsOD_GPSX, ptsOD_GPSY

	def get_all_nodes(self):
		nodes = self.genC + self.CoalDock + self.CoalSource + self.CoalIndBuffer
		return nodes

	def get_all_endpointsRef(self):
		"""
		retreive all the Coal grid line endpoints

		:param self: takes its own Coal grid object as an input
		:return: endpointsX: matrix of line origin and destination X coordinates of size lines*2 X refinements
		:return: endpointsY: matrix of line origin and destination X coordinates of size lines*2 X refinements
		"""
		endpointsX = sp.lil_matrix((len(self.CoalRailroad) * 2, len(self.refinements)))
		endpointsY = sp.lil_matrix((len(self.CoalRailroad) * 2, len(self.refinements)))
		for i, k1 in enumerate(self.CoalRailroad):
			endpointsX[i * 2, self.refinements.index(k1.refinement[0])] = k1.fBus[0]
			endpointsY[i * 2, self.refinements.index(k1.refinement[0])] = k1.fBus[1]
			endpointsX[i * 2 + 1, self.refinements.index(k1.refinement[0])] = k1.tBus[0]
			endpointsY[i * 2 + 1, self.refinements.index(k1.refinement[0])] = k1.tBus[1]
		return endpointsX, endpointsY

