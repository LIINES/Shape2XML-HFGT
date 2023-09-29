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

from ElectricGrid.GenC import GenC
from NGSystem.Terminal import Terminal
from NGSystem.Compressor import Compressor
from NGSystem.NGDelivery import NGDelivery
from NGSystem.NGProcessor import NGProcessor
from NGSystem.NGStorage import NGStorage
from NGSystem.NGPipe import NGPipe
from NGSystem.NGIndBuffer import NGIndBuffer

class NGGrid(object):
	"""
	This class represents the physical natural gas system which contains compressors, NG power plant, terminal, NG receipt delivery,
	NG pipeline, NG independent buffer, and NG pricing hub.

	Attributes:
		 genC					NG power plant
		 compressor				NG compressor
		 terminal      			NG terminal
		 NGReceiptDelivery      NG receipt delivery
		 NGProcessor			NG Processor
		 NGStorage				NG Storage
		 NGPricingHub   		NG pricing hub
		 NGIndBuffer       		NG independent buffer
		 NGPipe       			NG pipeline
		 buffer_map				dictionary of existing gps coords
		 refinements			list of refinements in the NG system
	"""

	def __init__(self):
		"""
		This function initializes all of the NGGrid attributes.
		:return: Empty NGGrid object
		"""
		self.name = self.__class__.__name__
		self.genC = []
		self.compressor = []
		self.terminal = []
		self.NGReceiptDelivery = []
		self.NGProcessor = []
		self.NGStorage = []
		self.NGPricingHub = []
		self.NGIndBuffer = []
		self.NGPipe = []
		self.buffer_map = {}
		self.refinements = ['electric power at 132kV', 'raw gas', 'processed gas', 'syngas']

	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def initialize_NG_system(self, datafiles):
		"""
		Instantiate the NG system by reading all the individual resource files. The
		compressors, NG power plant, terminal, NG receipt delivery, NG pipeline, NG independent buffer,
		and NG pricing hub are instantiated here.

		:param datafiles: List of shape files to read in
		:return:
		"""
		print('Instantiating NG System')
		self.instantiate_NGPowerPlant(datafiles)

		self.instantiate_terminal(datafiles)

		self.instantiate_NGReceiptDelivery(datafiles)

		self.instantiate_processor(datafiles)

		self.instantiate_NGStorage(datafiles)

		self.instantiate_compressor(datafiles)

		self.instantiate_NGIndBuffer(datafiles)

		self.instantiate_NGPricingHub(datafiles)

		self.instantiate_NGPipe(datafiles)

		return self

	def instantiate_NGPowerPlant(self, data):
		"""
		This function takes an input data list and instantiates all the genC.
		:param data: a list of all data files
		:return: NGGrid updated with all the genC
		"""
		print('Instantiating NG Power Plants')

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
				df = df[df['STATUS'] != 'NOT_OP']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_power_plants += 1
						continue

					plant_count += 1
					new_instance = GenC()
					new_instance.nodeType = 'GenC'
					new_instance.nodeName = 'NG Power Plant ' + str(plant_count)
					new_instance.genName = 'NG Power Plant ' + str(plant_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.cap = [max([instance['OP_CAP'], instance['SUMMER_CAP'], instance['WINTER_CAP']])]
					new_instance.fuelType = instance['FUEL_CAT']
					new_instance, fuels = self.set_fuel(new_instance, fuels)
					new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
					new_instance.status = 'true'
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

				skipped_power_plants = skipped_power_plants + init_plants - df.shape[0]
		return self

	def instantiate_terminal(self, data):
		"""
		This function takes as input data list and instantiates all the genS.
		:param data: a list of all data files
		:return: NGGrid updated with all the terminals
		"""
		print('Instantiating NG Terminals')

		terminal_count = 0
		fuels = set()
		skipped_terminals = 0
		for file in data:
			if 'Terminal' in file or '_LNG_' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('terminal file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# clean data based on status
				df = df[df['STATUS'] != 'Rejected']
				df = df[df['STATUS'] != 'Withdrawn']
				df = df[df['STATUS'] != 'Cancelled']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_terminals += 1
						continue

					terminal_count += 1
					new_instance = Terminal()
					new_instance.nodeType = 'terminal'
					new_instance.nodeName = 'NG Terminal ' + str(terminal_count)
					new_instance.termName = 'NG Terminal ' + str(terminal_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = instance['TYPE']
					new_instance, fuels = self.set_fuel(new_instance, fuels)
					new_instance.refinement = ['processed gas', 'syngas']
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.terminal.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.nodeName

					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])

				skipped_terminals = skipped_terminals + init_plants-df.shape[0]

		return self

	def instantiate_NGReceiptDelivery(self, data):
		"""
		This function takes as input data list and instantiates all the NG Receipt Delivery nodes.
		:param data: a list of all data files
		:return: NGGrid updated with all the Receipt Delivery nodes
		"""
		print('Instantiating NG Receipt Delivery')

		delivery_count = 0
		skipped_delivery = 0
		for file in data:
			if ('ReceiptDelivery' in file) or ('Receipt_Delivery' in file):
				try:
					df = gpd.read_file(file)
				except:
					print('ReceiptDelivery file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_delivery += 1
						continue

					delivery_count += 1
					new_instance = NGDelivery()
					new_instance.nodeType = 'NGReceiptDelivery'
					new_instance.nodeName = 'Receipt Delivery ' + str(delivery_count)
					new_instance.RDName = 'Receipt Delivery ' + str(delivery_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = ['raw gas', 'processed gas', 'syngas']
					new_instance.refinement = ['raw gas', 'processed gas', 'syngas']
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.NGReceiptDelivery.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.nodeName

		return self

	def instantiate_processor(self, data):
		"""
		This function takes as input data list and instantiates all the processors.
		:param data: a list of all data files
		:return: NGGrid updated with all the processors
		"""
		print('Instantiating NG Processing Plant')

		processor_count = 0
		skipped_processors = 0
		for file in data:
			if 'Processing' in file or 'Dehydrogenation' in file or 'Fractionation' in file or 'Steam_Crackers' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Processing file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				df = df[df['STATUS'] != 'Cancelled']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_processors += 1
						continue

					processor_count += 1
					new_instance = NGProcessor()
					new_instance.nodeType = 'NGProcessor'
					new_instance.nodeName = 'NG Processer ' + str(processor_count)
					new_instance.procName = 'NG Processer ' + str(processor_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = ['processed gas']
					new_instance.refinement = ['raw gas', 'processed gas']
					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.NGProcessor.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.nodeName
		return self

	def instantiate_NGStorage(self, data):
		"""
		This function takes as input data list and instantiates all the genS.
		:param data: a list of all data files
		:return: NGGrid updated with all the genS
		"""
		print('Instantiating NG Storage')

		storage_count = 0
		fuels = set()
		skipped_storage = 0
		for file in data:
			if 'Storage' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('NG Storage file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				df = df[df['STATUS'] != 'Rejected']
				df = df[df['STATUS'] != 'Abandoned']
				df = df[df['STATUS'] != 'Canceled']
				df = df[~df.STATUS.isnull()]
				df = df[~df.TYPE.isnull()]
				df = df.reset_index()

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_storage += 1
						continue

					storage_count += 1
					new_instance = NGStorage()
					new_instance.nodeType = 'NGStorage'
					new_instance.nodeName = 'NG Storage ' + str(storage_count)
					new_instance.storeName = 'NG Storage ' + str(storage_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = instance['TYPE']
					new_instance, fuels = self.set_fuel(new_instance, fuels)
					new_instance.refinement = new_instance.fuelType
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					try:
						new_instance.region = instance['REGION']
					except:
						print('No region attribute in .SHP file')
					self.NGStorage.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.nodeName

					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])

		return self

	def instantiate_compressor(self, data):
		"""
		This function takes as input data list and instantiates all the buses.
		:param data: a list of all data files
		:return: NGGrid updated with all the compressors
		"""
		print('Instantiating NG Compressors')

		compressor_count = 0
		skipped_compressors = 0
		for file in data:
			if 'Compressors' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('NG Storage file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x, 4), round(pnt.geoms[0].y, 4)) for pnt in df.geometry]

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_compressors += 1
						continue

					compressor_count += 1
					new_instance = Compressor()
					new_instance.nodeType = 'compressor'
					new_instance.nodeName = 'Compressor ' + str(compressor_count)
					new_instance.compName = 'Compressor ' + str(compressor_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = ['processed gas', 'syngas', 'raw gas']
					new_instance.refinement = ['processed gas', 'syngas', 'raw gas']
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.compressor.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.nodeName
					new_instance.status = 'true'

		return self

	def instantiate_NGIndBuffer(self, data):
		"""
		This function takes as input data list and instantiates all the independent buffers.
		:param data: a list of all data files
		:return: NGGrid updated with all the independent buffers
		"""

		return self

	def instantiate_NGPricingHub(self, data):
		"""
		This function takes as input data list and instantiates all the pricing hubs.
		:param data: a list of all data files
		:return: NGGrid updated with all the pricing hubs
		"""

		return self

	def instantiate_NGPipe(self, data):
		"""
		This function takes as input data list and instantiates all the branches.
		:param data: a list of all data files
		:return: NGGrid updated with all the pipelines
		"""
		print('Instantiating NG Pipelines')
		for file in data:
			if 'Pipelines' in file:
				df = gpd.read_file(file)
				try:
					df = gpd.read_file(file)
				except:
					print('NG Pipelines file doesnt exist: ' + file)
				line_count = 0
				skipped_Lines = 0
				dup = 0
				init_lines = df.shape[0]

				try:
					df = df[df['STATUS'] != 'Canceled']
				except:
					df = df[df['PROJSTATUS'] != 'Canceled']
				df = df[~df.geometry.boundary.is_empty]

				for index, instance in df.iterrows():
					line_count += 1
					new_instance = NGPipe()
					coords = [(round(pnt.x, 4), round(pnt.y, 4)) for pnt in instance.geometry.boundary]
					lineOrigin = coords[0]
					lineDest = coords[-1]
					new_instance.fBus = lineOrigin
					new_instance.tBus = lineDest
					new_instance.type = 'NGPipe'
					new_instance.lineName = 'Pipeline ' + str(line_count)
					new_instance.fuelType = ['processed gas', 'syngas', 'raw gas']
					new_instance.refinement = ['processed gas', 'syngas', 'raw gas']
					new_instance.status = 'true'
					self.NGPipe.append(new_instance)
				skipped_Lines = skipped_Lines + init_lines - df.shape[0]
		return self

	def set_fuel(self, node, fuels):
		"""
		This function takes as input node and set of fuels.
		:param node: node object
		:param fuels: set of fuels
		:return: node with updated fuel source and updated fuel set with unhandled fuels.
		"""
		if node.fuelType in (
		'BUTANE', 'METHANOL', 'COAL BED METHANE', 'METHANE', 'LANDFILL GAS', 'Natural Gas',
		'REFINERY GAS', 'Processed Gas', 'GAS (GENERIC)', 'NATURAL GAS', 'HYDROGEN', 'BLAST FURNACE GAS',
		'COKE OVEN GAS', 'LIQUIFIED PROPANE GAS', 'Depleted Field', 'Salt Cavern', 'Aquifer', 'LNG', 'Regasification'):
			node.fuelType = 'processed gas'
		elif node.fuelType in (
		'DISTILLATE OIL', 'NO. 1 FUEL OIL', 'NO. 6 FUEL OIL', 'KEROSENE', 'Oil', 'NO. 2 FUEL OIL', 'PETROLEUM COKE',
		'DIESEL FUEL', 'COKE', 'HFO', 'NO. 5 FUEL OIL', 'RESIDUAL OILS', 'NO. 4 FUEL OIL', 'BLACK LIQUOR',
		'REFUSED DERIVED FUEL', 'JET FUEL', 'FUEL OIL', 'Liquefaction','Non-HVL Products'):
			node.fuelType = 'processed oil'
		elif node.fuelType in ('CRUDE OIL', 'Crude Oil','Crude','Condensate','Crude/Condensate', 'Converting to Crude', 'Crude Butadiene','Crude Oil/Condensate'):
			node.fuelType = 'crude oil'
		elif node.fuelType in (
		'LIGNITE COAL GAS (FROM COAL GASIFICATION)', 'WOOD GAS (FROM WOOD GASIFICATION)', 'ANTHRACITE',
		'GAS FROM REFUSE GASIFICATION', 'GAS FROM REFUSE GASIFICATION', 'WOOD GAS (FROM WOOD GASIFICATION)',
		'GAS FROM BIOMASS GASIFICATION', 'COAL GAS (FROM COAL GASIFICATION)', 'GAS FROM FUEL OIL GASIFICATION',
		'BITUMINOUS COAL GAS (FROM COAL GASIFICATION)'):
			node.fuelType = 'syngas'
		elif node.fuelType in ('WASTE COAL', 'GOB', 'COAL (GENERIC)', 'LIGNITE', 'Coal', 'SUBBITUMINOUS', 'BITUMINOUS COAL'):
			node.fuelType = 'coal'
		elif node.fuelType in ('URANIUM', 'Uranium'):
			node.fuelType = 'uranium'
		elif node.fuelType in ('AGRICULTURAL WASTE', 'REFUSE', 'MANURE', 'BIOMASS', 'TIRES', 'POULTRY LITTER'):
			node.fuelType = 'solid biomass feedstock'
		elif node.fuelType in ('WASTE WATER SLUDGE', 'DIGESTER GAS (SEWAGE SLUDGE GAS)', 'BIODIESEL', 'WASTE GAS', 'GEOTHERMAL STEAM',
		'WOOD WASTE LIQUIDS EXCL BLK LIQ (INCL RED LIQUOR,SLUDGE WOOD,SPENT SULFITE LIQUOR AND OTH LIQUIDS)'):
			node.fuelType = 'liquid biomass feedstock'
		elif node.fuelType in ('Water', 'Water Energy'):
			node.fuelType = 'water energy'
		elif node.fuelType in ('Solar', 'SOLAR'):
			node.fuelType = 'solar'
		elif node.fuelType in ('Wind', 'WIND'):
			node.fuelType = 'wind energy'
		elif node.fuelType in ('Other', 'WASTE HEAT', 'STEAM', 'UNKNOWN', 'COMPRESSED AIR', 'NOT APPLICABLE', 'Unknown'):
			node.fuelType = 'other'
		else:
			print('Found a new fuel type that needs to be handled')
			print(node.nodeName)
			print(node.fuelType)
			fuels.add(node.fuelType)

		if node.fuelType not in self.refinements:
			self.refinements.append(node.fuelType)

		node.fuelType = [node.fuelType]

		return node, fuels

	def getPtsGPSRef(self):
		"""
		retreive all the X and Y coordinates of all buffers and line endpoints

		:param self: takes its own NG grid object as an input
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
		"""
		retreive all the NG grid nodes

		:param self: takes its own NG grid object as an input
		:return: nodes: list of all buffer objects
		"""
		nodes = self.genC + self.compressor + self.terminal + self.NGReceiptDelivery + self.NGProcessor + self.NGIndBuffer
		return nodes

	def get_all_endpointsRef(self):
		"""
		retreive all the NG grid line endpoints

		:param self: takes its own NG grid object as an input
		:return: endpointsX: matrix of line origin and destination X coordinates of size lines*2 X refinements
		:return: endpointsY: matrix of line origin and destination X coordinates of size lines*2 X refinements
		"""
		endpointsX = sp.lil_matrix((len(self.NGPipe) * 2, len(self.refinements)))
		endpointsY = sp.lil_matrix((len(self.NGPipe) * 2, len(self.refinements)))
		for i, k1 in enumerate(self.NGPipe):
			endpointsX[i * 2, self.refinements.index(k1.refinement[0])] = k1.fBus[0]
			endpointsY[i * 2, self.refinements.index(k1.refinement[0])] = k1.fBus[1]
			endpointsX[i * 2 + 1, self.refinements.index(k1.refinement[0])] = k1.tBus[0]
			endpointsY[i * 2 + 1, self.refinements.index(k1.refinement[0])] = k1.tBus[1]
		return endpointsX, endpointsY

	def get_num_transporters(self):
		return len(self.NGPipe)