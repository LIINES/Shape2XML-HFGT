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
import xml.etree.ElementTree as ET
from collections import OrderedDict

from ElectricGrid.ElectricLine import ElectricLine
from ElectricGrid.Bus import Bus
from ElectricGrid.GenC import GenC
from ElectricGrid.GenS import GenS
from ElectricGrid.LoadC import LoadC
from ElectricGrid.LoadS import LoadS
from ElectricGrid.StorageC import StorageC
from ElectricGrid.StorageS import StorageS

class ElectricGrid(object):
	"""
	This class represents the physical electric grid which contains buses, branches, load, generators,
	and storage elements.

	Attributes:
		 bus        	power system buses
		 electricLine   power systems electricLine
		 loadS      	stochastic loads
		 loadC      	controllable loads
		 genC       	controllable generators
		 genS       	stochastic generators
		 storageS   	stochastic storage
		 storageC   	controllable storage
	"""

	def __init__(self):
		"""
		This function initializes all of the ElectricGrid attributes.
		:return: Empty ElectricGrid object
		"""
		self.name = self.__class__.__name__
		self.bus = []
		self.electricLine = []
		self.loadS = []
		self.loadC = []
		self.genS = []
		self.genC = []
		self.storageS = []
		self.storageC = []
		self.buffer_map = {}
		self.refinements = ['electric power at 132kV']

	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def initialize_electric_grid(self, datafiles):
		"""
		Instantiate the electricGrid by reading all the individual resource files. The
		generators, buses, electricLine and loads are instantiated here.

		:param datafiles: List of shape files to read in
		:return:
		"""
		print('Instantiating Electric Grid')
		self.instantiate_buses(datafiles)

		self.instantiate_gen_c(datafiles)

		self.instantiate_gen_s(datafiles)

		self.instantiate_load_c(datafiles)

		self.instantiate_load_s(datafiles)

		self.instantiate_storage_c(datafiles)

		self.instantiate_storage_s(datafiles)

		self.instantiate_electricLine(datafiles)

		return self

	def instantiate_buses(self, data):
		"""
		This function takes as input data list and instantiates all the buses.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the buses
		"""
		# print('Overwrite this sub-initializing function for project specific Bus handling')

		return self

	def instantiate_gen_c(self, data):
		"""
		This function takes as input data list and instantiates all the genC.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the genC
		"""
		print("Instantiating GenC")

		fuels = set()
		plant_count = 0
		storage_count = 0
		skipped_power_plants = 0
		for file in data:
			if 'PowerPlant' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('PowerPlant file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# Clean Data based on Status
				df = df[df['STATUS']!='NOT_OP']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				# iterate over each powerplant
				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map: # Skip if overlapping with existing node
						skipped_power_plants += 1
						continue

					if instance['PRIME_MVR1'] == 'Pumped Storage':  # Handle Storage node
						storage_count += 1
						new_instance = StorageC()
						new_instance.nodeType = 'StoreC'
						new_instance.nodeName = 'Pump Storage ' + str(storage_count)
						new_instance.storageCName = 'Pump Storage ' + str(storage_count)
						new_instance.gpsX = coords[index][0]
						new_instance.gpsY = coords[index][1]
						new_instance.cap = [max([instance['OP_CAP'], instance['SUMMER_CAP'], instance['WINTER_CAP']])]
						new_instance.fuelType = instance['FUEL_CAT']
						[new_instance, fuels] = self.set_fuel(new_instance, fuels)
						new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
						new_instance.status = True
						try:
							new_instance.state = instance['STUSPS']
						except:
							print('No state attribute in .SHP file')
						try:
							new_instance.iso = instance['ISO']
						except:
							print('No ISO attribute in .SHP file')
						self.storageC.append(new_instance)
						self.buffer_map[coords[index]] = new_instance.nodeName
					elif (instance['PRIME_MVR1'] == 'Wind Turbine' or instance['PRIME_MVR1'] == 'Solar'):  # Handle stocastic renewable nodes
						plant_count += 1
						new_instance = GenS()
						new_instance.nodeType = 'GenS'
						new_instance.nodeName = 'Power Plant ' + str(plant_count)
						new_instance.genName = 'Power Plant ' + str(plant_count)
						new_instance.gpsX = coords[index][0]
						new_instance.gpsY = coords[index][1]
						new_instance.cap = [max([instance['OP_CAP'], instance['SUMMER_CAP'], instance['WINTER_CAP']])]
						new_instance.fuelType = instance['FUEL_CAT']
						new_instance, fuels = self.set_fuel(new_instance, fuels)
						new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
						new_instance.status = True
						try:
							new_instance.state = instance['STUSPS']
						except:
							print('No state attribute in .SHP file')
						try:
							new_instance.iso = instance['ISO']
						except:
							print('No ISO attribute in .SHP file')
						self.genS.append(new_instance)
						self.buffer_map[coords[index]] = new_instance.nodeName
					else:  # handle conventional power plant
						plant_count += 1
						new_instance = GenC()
						new_instance.nodeType = 'GenC'
						new_instance.nodeName = 'Power Plant ' + str(plant_count)
						new_instance.genName = 'Power Plant ' + str(plant_count)
						new_instance.gpsX = coords[index][0]
						new_instance.gpsY = coords[index][1]
						new_instance.cap = [max([instance['OP_CAP'], instance['SUMMER_CAP'], instance['WINTER_CAP']])]
						new_instance.fuelType = instance['FUEL_CAT']
						new_instance, fuels = self.set_fuel(new_instance, fuels)
						new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
						new_instance.status = True
						try:
							new_instance.state = instance['STUSPS']
						except:
							print('No state attribute in .SHP file')
						try:
							new_instance.iso = instance['ISO']
						except:
							print('No ISO attribute in .SHP file')
						self.genC.append(new_instance)
						self.buffer_map[coords[index]] = new_instance.nodeName

					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])
				skipped_power_plants = skipped_power_plants + init_plants-df.shape[0]

			if 'GenUnits' in file:
				df = gpd.read_file(file)
				init_gens = df.shape[0]

				# Clean data based on status
				df = df[df['STATUS']!='RETIRED']
				df = df[df['STATUS']!='CANCELLED']
				df = df[df['STATUS']!='STANDBY']
				df = df[df['STATUS']!='SOLD AND DISMANTLED (WAS: SOLD TO AND OPERATED BY NON-UTILITY)']
				df = df[df['STATUS']!='PROPOSED']
				df = df[df['STATUS']!='PLANNED GENERATOR INDEFINITELY POSTPONED']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				# iterate over each Gen Unit
				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:  # Skip if overlapping with existing node
						skipped_power_plants += 1
						continue

					if instance['PRIME_MVR'] == 'PUMPED STORAGE':  # Handle Storage node
						storage_count += 1
						new_instance = StorageC()
						new_instance.nodeType = 'StoreC'
						new_instance.nodeName = 'Pump Storage ' + str(storage_count)
						new_instance.storageCName = 'Pump Storage ' + str(storage_count)
						new_instance.gpsX = coords[index][0]
						new_instance.gpsY = coords[index][1]
						new_instance.cap = [instance['OP_CAP']]
						new_instance.fuelType = instance['FUEL1']
						new_instance, fuels = self.set_fuel(new_instance, fuels)
						new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
						new_instance.status = True
						try:
							new_instance.state = instance['STUSPS']
						except:
							print('No state attribute in .SHP file')
						try:
							new_instance.iso = instance['ISO']
						except:
							print('No ISO attribute in .SHP file')
						self.storageC.append(new_instance)
						self.buffer_map[coords[index]] = new_instance.nodeType
					elif instance['PRIME_MVR'] == 'SOLAR' or instance['PRIME_MVR'] == 'WIND TURBINE':  # Handle stochastic generator: solar, wind
						plant_count += 1
						new_instance = GenS()
						new_instance.nodeType = 'GenS'
						new_instance.nodeName = 'Power Plant ' + str(plant_count)
						new_instance.genName = 'Power Plant ' + str(plant_count)
						new_instance.gpsX = coords[index][0]
						new_instance.gpsY = coords[index][1]
						new_instance.cap = [instance['OP_CAP']]
						new_instance.fuelType = instance['FUEL1']
						new_instance, fuels = self.set_fuel(new_instance, fuels)
						new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
						new_instance.status = True
						try:
							new_instance.state = instance['STUSPS']
						except:
							print('No state attribute in .SHP file')
						try:
							new_instance.iso = instance['ISO']
						except:
							print('No ISO attribute in .SHP file')
						self.genS.append(new_instance)
						self.buffer_map[coords[index]] = new_instance.nodeName
					else:  # Handle controlled generator: all else, including water/hydro
						plant_count += 1
						new_instance = GenC()
						new_instance.nodeType = 'GenC'
						new_instance.nodeName = 'Power Plant ' + str(plant_count)
						new_instance.genName = 'Power Plant ' + str(plant_count)
						new_instance.gpsX = coords[index][0]
						new_instance.gpsY = coords[index][1]
						new_instance.cap = [instance['OP_CAP']]
						new_instance.fuelType = instance['FUEL1']
						new_instance, fuels = self.set_fuel(new_instance, fuels)
						new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
						new_instance.status = True
						try:
							new_instance.state = instance['STUSPS']
						except:
							print('No state attribute in .SHP file')
						try:
							new_instance.iso = instance['ISO']
						except:
							print('No ISO attribute in .SHP file')
						self.genC.append(new_instance)
						self.buffer_map[coords[index]] = new_instance.nodeName

					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])

				skipped_power_plants = skipped_power_plants + init_gens-df.shape[0]

		return self

	def instantiate_gen_s(self, data):
		"""
		This function takes as input data list and instantiates all the genS.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the genS
		"""

		return self

	def instantiate_load_s(self, data):
		"""
		This function takes as input data list and instantiates all the loadS.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the loadS
		"""

		return self

	def instantiate_load_c(self, data):
		"""
		This function takes as input data list and instantiates all the loadC.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the loadC
		"""
		print("Instantiating LoadC")
		for file in data:
			if 'Substations' in file:
				df = gpd.read_file(file)
				substation_count = 0
				skipped_substations = 0
				init_stations = df.shape[0]

				# Clean Data based on Status
				df = df[df['STATUS']!='CN']
				df = df[df['CHAR_ID']!='-99']
				df = df[df['CHAR_ID']!='-98']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				# iterate over each load
				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:  # Skip if overlapping with existing node
						skipped_substations += 1
						continue
					substation_count += 1
					new_instance = LoadC()
					new_instance.nodeType = 'LoadC'
					new_instance.nodeName = 'Substation ' + str(substation_count)
					new_instance.loadName = 'Substation ' + str(substation_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.loadCType = 'electric power at 132kV'
					new_instance.refinement = ['electric power at 132kV']
					new_instance.status = True
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					try:
						new_instance.iso = instance['ISO']
					except:
						print('No ISO attribute in .SHP file')
					self.loadC.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.nodeName

				skipped_substations = skipped_substations + init_stations-df.shape[0]

		return self

	def instantiate_storage_s(self, data):
		"""
		This function takes as input data list and instantiates all the storageS.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the storageS
		"""

		return self

	def instantiate_storage_c(self, data):
		"""
		This function takes as input data list and instantiates all the storageC.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the storageC
		"""

		return self

	def instantiate_electricLine(self, data):
		"""
		This function takes as input data list and instantiates all the branches.
		:param data: a list of all data files
		:return: ElectricGrid updated with all the branches
		"""
		print("Instantiating Transmission")

		for file in data:
			if 'Transmission' in file:
				df = gpd.read_file(file)
				transmission_count = 0
				skipped_Lines = 0
				init_lines = df.shape[0]

				df = df[~df.geometry.boundary.is_empty]  # Remove lines without GPS coords
				# iterate over each line
				for index, instance in df.iterrows():
					# print('instance %d of %d' % (index+1, df.shape[0]))

					# round the line coords
					coords = [(round(pnt.x, 4), round(pnt.y, 4)) for pnt in instance.geometry.boundary]

					new_instance = ElectricLine()
					lineOrigin = coords[0]
					lineDest = coords[-1]
					new_instance.fBus = lineOrigin
					new_instance.tBus = lineDest
					new_instance.fBus_gps = lineOrigin
					new_instance.tBus_gps = lineDest
					dup = 0
					for line in self.electricLine:  # check to see if the line already exists
						if (new_instance.fBus == line.fBus and new_instance.tBus == line.tBus) \
								or (new_instance.fBus == line.tBus and new_instance.tBus == line.fBus):
							dup = 1
							break
					if dup == 1:
						skipped_Lines += 1
						continue

					transmission_count += 1
					new_instance.lineName = 'Transmission Line ' + str(transmission_count)
					new_instance.refinement = ['electric power at 132kV']
					self.electricLine.append(new_instance)

				skipped_Lines = skipped_Lines + init_lines-df.shape[0]

		return self

	def set_fuel(self, node, fuels):
		"""
		This function takes as input node and set of fuels.
		:param node: node object
		:param fuels: set of fuels
		:return: node with updated fuel source and updated fuel set with unhandled fuels.
		"""
		if node.fuelType in ('BUTANE', 'METHANOL', 'COAL BED METHANE', 'METHANE', 'LANDFILL GAS', 'Natural Gas','REFINERY GAS',
							 'Processed Gas', 'GAS (GENERIC)', 'NATURAL GAS', 'HYDROGEN','BLAST FURNACE GAS',
							 'COKE OVEN GAS', 'LIQUIFIED PROPANE GAS', 'Depleted Field', 'Salt Cavern', 'Aquifer', 'LNG',
							 'Hydrogen','Hydrogen Gas', 'Nitrogen','Other Gas', 'Empty Gas', 'Natural Gas Liquids', 'Regasification'):
			node.fuelType = 'processed gas'
		elif node.fuelType in ('DISTILLATE OIL', 'NO. 1 FUEL OIL', 'NO. 6 FUEL OIL', 'KEROSENE', 'Oil', 'NO. 2 FUEL OIL', 'PETROLEUM COKE',
							'DIESEL FUEL', 'COKE', 'HFO', 'NO. 5 FUEL OIL', 'RESIDUAL OILS', 'NO. 4 FUEL OIL', 'BLACK LIQUOR', 'REFUSED DERIVED FUEL',
							'JET FUEL', 'FUEL OIL', 'Non-HVL Product', 'Non_HVL Products', 'Gasoline', 'Empty Liquid', 'Fuel Oil NO. 6',
							'Fuel Oil', 'processed oil', 'Liquefied Petroleum Gas', 'Fuel Oil, Kerosene, Gasoline, Jet, Diesel',
							'Fuel Grade Ethanol', 'Highly Volatile Liquid', 'Refined Products', 'Empty Hazardous Liquid or Gas', 'Unleaded Gasoline', 'Non-HVL Products'):
			node.fuelType = 'processed oil'
		elif node.fuelType in ('CRUDE OIL', 'Crude Oil'):
			node.fuelType = 'crude oil'
		elif node.fuelType in ('LIGNITE COAL GAS (FROM COAL GASIFICATION)', 'WOOD GAS (FROM WOOD GASIFICATION)', 'ANTHRACITE',
							   'GAS FROM REFUSE GASIFICATION',
							   'GAS FROM BIOMASS GASIFICATION','COAL GAS (FROM COAL GASIFICATION)','GAS FROM FUEL OIL GASIFICATION',
							   'BITUMINOUS COAL GAS (FROM COAL GASIFICATION)'):
			node.fuelType = 'syngas'
		elif node.fuelType in ('WASTE COAL', 'GOB','COAL (GENERIC)','LIGNITE','Coal', 'SUBBITUMINOUS','BITUMINOUS COAL'):
			node.fuelType = 'coal'
		elif node.fuelType in ('URANIUM', 'Uranium'):
			node.fuelType = 'uranium'
		elif node.fuelType in ('AGRICULTURAL WASTE', 'REFUSE', 'MANURE', 'BIOMASS', 'TIRES', 'POULTRY LITTER','WOOD AND WOOD WASTE'):
			node.fuelType = 'solid biomass feedstock'
		elif node.fuelType in ('WASTE WATER SLUDGE', 'DIGESTER GAS (SEWAGE SLUDGE GAS)', 'BIODIESEL', 'WASTE GAS', 'GEOTHERMAL STEAM',
							   'WOOD WASTE LIQUIDS EXCL BLK LIQ (INCL RED LIQUOR,SLUDGE WOOD,SPENT SULFITE LIQUOR AND OTH LIQUIDS)'):
			node.fuelType = 'liquid biomass feedstock'
		elif node.fuelType in ('Water', 'Water Energy', 'WATER'):
			node.fuelType = 'water energy'
		elif node.fuelType in ('Solar', 'SOLAR'):
			node.fuelType = 'solar'
		elif node.fuelType in ('Wind', 'WIND'):
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

		:param self: takes its own electric grid object as an input
		:return: ptsB_GPSX: matrix of buffer X coordinates of size buffers X refinements
		:return: ptsB_GPSY: matrix of buffer Y coordinates of size buffers X refinements
		:return: ptsOD_GPSX: matrix of line origin and destination X coordinates of size lines*2 X refinements
		:return: ptsOD_GPSY: matrix of line origin and destination Y coordinates of size lines*2 X refinements
		"""
		print('Entering getPtsGPSRef')
		ptsB = self.get_all_nodes()
		ptsODX, ptsODY = self.get_all_endpointsRef()

		ptsB_GPSX = sp.lil_matrix((len(ptsB), len(self.refinements)))
		ptsB_GPSY = sp.lil_matrix((len(ptsB), len(self.refinements)))
		for i, k1 in enumerate(ptsB):
			for k2 in k1.refinement:
				ptsB_GPSX[i, self.refinements.index(k2)] = k1.gpsX
				ptsB_GPSY[i, self.refinements.index(k2)] = k1.gpsY

		ptsOD_GPSX = ptsODX
		ptsOD_GPSY = ptsODY

		return ptsB_GPSX, ptsB_GPSY, ptsOD_GPSX, ptsOD_GPSY

	def get_all_nodes(self):
		"""
		retreive all the electric grid nodes

		:param self: takes its own electric grid object as an input
		:return: nodes: list of all buffer objects
		"""
		nodes = self.genC + self.genS + self.storageC + self.storageS + self.loadC + self.loadS + self.bus
		return nodes

	def get_num_nodes(self):
		"""
		retreive all the electric grid nodes

		:param self: takes its own electric grid object as an input
		:return: num_nodes: total number of buffer objects
		"""
		num_nodes = len(self.genC) + len(self.genS) + len(self.storageC) + len(self.storageS) + len(self.loadC) + len(self.loadS) + len(self.bus)
		return num_nodes

	def get_all_endpointsRef(self):
		"""
		retreive all the electric grid line endpoints

		:param self: takes its own electric grid object as an input
		:return: endpointsX: matrix of line origin and destination X coordinates of size lines*2 X refinements
		:return: endpointsY: matrix of line origin and destination X coordinates of size lines*2 X refinements
		"""
		endpointsX = sp.lil_matrix((len(self.electricLine)*2, len(self.refinements)))
		endpointsY = sp.lil_matrix((len(self.electricLine)*2, len(self.refinements)))
		for i, k1 in enumerate(self.electricLine):
			endpointsX[i*2, self.refinements.index(k1.refinement[0])] = k1.fBus[0]
			endpointsY[i*2, self.refinements.index(k1.refinement[0])] = k1.fBus[1]
			endpointsX[i*2+1, self.refinements.index(k1.refinement[0])] = k1.tBus[0]
			endpointsY[i*2+1, self.refinements.index(k1.refinement[0])] = k1.tBus[1]
		return endpointsX, endpointsY