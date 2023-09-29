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
from OilSystem.OilTerminal import OilTerminal
from OilSystem.OilPort import OilPort
from OilSystem.OilRefinery import OilRefinery
from OilSystem.OilCrudePipe import OilCrudePipe
from OilSystem.OilRefPipe import OilRefPipe
from OilSystem.OilIndBuffer import OilIndBuffer

class OilGrid(object):
	"""
	This class represents the physical oil system which contains oil power plant, terminal,
	oil pipelines, oil independent buffer, and oil refinery, and oil port.

	Attributes:
		 genC					NG power plant
		 OilTerminal			oil terminal
		 OilPorts      			oil port
		 OilRefineries      	oil refineries
		 OilIndBuffer			oil independent buffer
		 OilCrudePipe			crude oil pipe
		 OilRefPipe   			refined oil pipe
		 buffer_map				dictionary of existing gps coords
		 refinements			list of refinements in the NG system
		 roads       			NG independent buffer
		 NGPipe       			NG pipeline
	"""

	def __init__(self):
		"""
		This function initializes all of the OilGrid attributes.
		:return: Empty OilGrid object
		"""
		self.name = self.__class__.__name__
		self.genC = []
		self.OilTerminal = []
		self.OilPorts = []
		self.OilRefineries = []
		self.OilIndBuffer = []
		self.OilCrudePipe = []
		self.OilRefPipe = []
		self.roads = []
		self.buffer_map = {}
		self.refinements = ['processed oil', 'crude oil', 'liquid biomass feedstock', 'processed gas']

	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def initialize_Oil_system(self, datafiles):
		"""
		Instantiate the OilGrid by reading all the individual resource files. The
		oil power plant, terminal, oil pipelines, oil independent buffer, oil refinery, and oil port.

		:param datafiles: List of shape files to read in
		:return:
		"""
		print('Instantiating Oil System')

		self.instantiate_OilPowerPlant(datafiles)

		self.instantiate_OilTerminal(datafiles)

		self.instantiate_OilPorts(datafiles)

		self.instantiate_OilRefineries(datafiles)

		self.instantiate_OilIndBuffer(datafiles)

		self.instantiate_OilCrudePipe(datafiles)

		self.instantiate_OilRefinedPipe(datafiles)

		return self

	def instantiate_OilPowerPlant(self, data):
		"""
		This function takes an input data list and instantiates all the genC.
		:param data: a list of all data files
		:return: OilGrid updated with all the genC
		"""
		print('Instantiating Oil Power Plants')

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

				for index, instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_power_plants += 1
						continue

					plant_count += 1
					new_instance = GenC()
					new_instance.nodeName = 'Oil Power Plant ' + str(plant_count)
					new_instance.genName = 'Oil Power Plant ' + str(plant_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.cap = [max([instance['OP_CAP'], instance['SUMMER_CAP'], instance['WINTER_CAP']])]
					new_instance.fuelType = instance['FUEL_CAT']
					new_instance, fuels = self.set_fuel(new_instance, fuels)
					new_instance.refinement = ['electric power at 132kV'] + new_instance.fuelType
					new_instance.status = 'true'
					new_instance.type = 'buffer'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					try:
						new_instance.iso = instance['ISO']
					except:
						print('No ISO attribute in .SHP file')
					self.genC.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.genName
					for k1 in new_instance.refinement:
						if k1 not in self.refinements:
							self.refinements.append(k1)

				skipped_power_plants = skipped_power_plants + init_plants-df.shape[0]

		return self

	def instantiate_OilTerminal(self, data):
		"""
		This function takes as input data list and instantiates all the terminals.
		:param data: a list of all data files
		:return: OilGrid updated with all the terminals
		"""
		print('Instantiating Oil Terminals')

		OilTerminal_count = 0
		for file in data:
			if 'Terminal' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Terminal file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				df = df[df['STATUS']!='Rejected']
				df = df[df['STATUS']!='Withdrawn']
				df = df[~df.STATUS.isnull()]
				df = df.reset_index()
				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				for index,instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_terminals += 1
						continue

					OilTerminal_count += 1
					new_instance = OilTerminal()
					new_instance.nodeName = 'Oil Terminal ' + str(OilTerminal_count)
					new_instance.termName = 'Oil Terminal ' + str(OilTerminal_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = ['processed oil', 'crude oil', 'liquid biomass feedstock', 'processed gas']
					new_instance.refinement = new_instance.fuelType
					new_instance.status = 'true'
					new_instance.type = 'buffer'
					new_instance.overlap = []
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.OilTerminal.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.termName

		print('Oil terminal count is ' + str(OilTerminal_count))
		return self

	def instantiate_OilPorts(self, data):
		"""
		This function takes as input data list and instantiates all the ports.
		:param data: a list of all data files
		:return: OilPorts updated with all the ports
		"""
		print('Instantiating Oil Ports')

		OilPorts_count = 0
		skipped_OilPorts = 0
		for file in data:
			if 'Port' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Port file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				for index,instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_OilPorts += 1
						continue

					OilPorts_count += 1
					new_instance = OilPort()
					new_instance.nodeName = 'Oil Port ' + str(OilPorts_count)
					new_instance.portName = 'Oil Port ' + str(OilPorts_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = ['processed oil', 'crude oil']
					new_instance.refinement = new_instance.fuelType
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.OilPorts.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.portName

		return self

	def instantiate_OilRefineries(self, data):
		"""
		This function takes as input data list and instantiates all the refineries.
		:param data: a list of all data files
		:return: OilGrid updated with all the refineries
		"""
		print('Instantiating Oil Refineries')

		OilRefineries_count = 0
		skipped_OilRefineries = 0
		for file in data:
			if 'Refineries' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('Refineries file doesnt exist: ' + file)
					continue
				init_plants = df.shape[0]

				# round coordinates to 4 decimal points for consistency
				coords = [(round(pnt.geoms[0].x,4),round(pnt.geoms[0].y,4)) for pnt in df.geometry]

				for index,instance in df.iterrows():
					if coords[index] in self.buffer_map:
						skipped_OilRefineries += 1
						continue

					OilRefineries_count += 1
					new_instance = OilRefinery()
					new_instance.nodeName = 'Oil Refinery ' + str(OilRefineries_count)
					new_instance.refName = 'Oil Refinery ' + str(OilRefineries_count)
					new_instance.gpsX = coords[index][0]
					new_instance.gpsY = coords[index][1]
					new_instance.fuelType = ['processed oil', 'crude oil']
					new_instance.refinement = ['processed oil', 'crude oil']
					new_instance.status = 'true'
					try:
						new_instance.state = instance['STUSPS']
					except:
						print('No state attribute in .SHP file')
					self.OilRefineries.append(new_instance)
					self.buffer_map[coords[index]] = new_instance.refName

		return self

	def instantiate_OilIndBuffer(self, data):
		"""
		This function takes as input data list and instantiates all the independent buffers.
		:param data: a list of all data files
		:return: OilGrid updated with all the independent buffers
		"""

		return self

	def instantiate_OilCrudePipe(self, data):
		"""
		This function takes as input data list and instantiates all the crude pipes.
		:param data: a list of all data files
		:return: OilGrid updated with all the Crude Pipes
		"""
		print('Instantiating Crude Oil Pipelines')
		fuels = set()
		for file in data:
			if 'CrudePipeline' in file or 'Oil_Pipelines' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('CrudePipeline file doesnt exist: ' + file)
					continue
				OilCrudePipe_count = 0
				init_OilCrudePipe = df.shape[0]

				df = df[df['STATUS']!='Shut Down']
				df = df[~df.geometry.boundary.is_empty]
				df = df[~df.PRODUCT.isnull()]

				for index,instance in df.iterrows():
					coords = [(round(pnt.x,4),round(pnt.y,4)) for pnt in instance.geometry.boundary]

					OilCrudePipe_count += 1
					new_instance = OilCrudePipe()
					lineOrigin = coords[0]
					lineDest = coords[-1]
					new_instance.fBus = lineOrigin
					new_instance.tBus = lineDest
					new_instance.lineName = 'Crude Pipeline ' + str(OilCrudePipe_count)
					new_instance.refinement = 'crude oil'
					new_instance.fuelType = instance['PRODUCT']
					[new_instance, fuels] = self.set_fuel(new_instance, fuels)
					new_instance.refinement = new_instance.fuelType
					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])
					new_instance.status = 'true'
					self.OilCrudePipe.append(new_instance)

				skipped_OilCrudePipe = init_OilCrudePipe-df.shape[0]
		return self

	def instantiate_OilRefinedPipe(self, data):
		"""
		This function takes as input data list and instantiates all the refined pipelines.
		:param data: a list of all data files
		:return: OilGrid updated with all the refined pipeines
		"""
		print('Instantiating refined Oil Pipelines')
		fuels = set()
		for file in data:
			if 'RefinedPipeline' in file or 'Refined_Product' in file:
				try:
					df = gpd.read_file(file)
				except:
					print('refined Pipeline file doesnt exist: ' + file)
					continue
				OilRefPipe_count = 0
				skipped_OilRefPipe = 0
				init_OilRefPipe = df.shape[0]

				df = df[df['PROJSTATUS'] != 'Out of Service']
				df = df[df['PROJSTATUS'] != 'Shut Down']
				df = df[~df.geometry.boundary.is_empty]
				df = df[~df.PRODUCT.isnull()]

				for index,instance in df.iterrows():
					coords = [(round(pnt.x,4),round(pnt.y,4)) for pnt in instance.geometry.boundary]

					OilRefPipe_count += 1
					new_instance = OilRefPipe()
					lineOrigin = coords[0]
					lineDest = coords[-1]
					new_instance.fBus = lineOrigin
					new_instance.tBus = lineDest
					new_instance.lineName = 'Refined Pipeline ' + str(OilRefPipe_count)
					new_instance.fuelType = instance['PRODUCT']
					[new_instance, fuels] = self.set_fuel(new_instance, fuels)
					new_instance.refinement = new_instance.fuelType
					if new_instance.fuelType[0] not in self.refinements:
						self.refinements.append(new_instance.fuelType[0])
					new_instance.status = 'true'
					self.OilRefPipe.append(new_instance)

				skipped_OilRefPipe = skipped_OilRefPipe + init_OilRefPipe-df.shape[0]

		return self

	def set_fuel(self, node, fuels):
		"""
		This function takes as input node and set of fuels.
		:param node: node object
		:param fuels: set of fuels
		:return: node with updated fuel source and updated fuel set with unhandled fuels.
		"""
		if node.fuelType in ('BUTANE', 'METHANOL', 'COAL BED METHANE', 'METHANE', 'LANDFILL GAS', 'Natural Gas',
		'REFINERY GAS', 'Processed Gas', 'GAS (GENERIC)', 'NATURAL GAS', 'HYDROGEN', 'BLAST FURNACE GAS', 'COKE OVEN GAS',
		'LIQUIFIED PROPANE GAS', 'Depleted Field', 'Salt Cavern', 'Aquifer', 'LNG', 'Hydrogen','Hydrogen Gas', 'Nitrogen',
		'Other Gas', 'Empty Gas', 'Natural Gas Liquids','Propane, Propylene','Butane Mix','Co2 Cont. Csgh Gas','Fuel Gas Line','Butane, Propane',
		'Landfill Gas','Propane, Butane','Heavy Aromatics','Chlorine Gas','Propane, Ethane, Propylene','Ethane, Propane','Propylene Oxide','Pentane',
		'Butane, Butylene','Butane, Isobutane, Natural Gas','Refinery Gas','Butene','Butane Vapor', 'Gas Lift','Flare Gas','Supply Gas',
		'High BTU Gas','High BTU Gas Line','Gas and Oil','LNG, Refined Products', 'Butane','Ethane, Propane, Butane','Helium, Nitrogen'):
			node.fuelType = 'processed gas'
		elif node.fuelType in ('DISTILLATE OIL', 'NO. 1 FUEL OIL', 'NO. 6 FUEL OIL', 'KEROSENE', 'Oil', 'NO. 2 FUEL OIL', 'PETROLEUM COKE',
		'DIESEL FUEL', 'COKE', 'HFO', 'NO. 5 FUEL OIL', 'RESIDUAL OILS', 'NO. 4 FUEL OIL', 'BLACK LIQUOR',
		'REFUSED DERIVED FUEL', 'JET FUEL', 'Jet Fuel', 'FUEL OIL', 'Non-HVL Product','Non_HVL Products', 'Gasoline', 'Empty Liquid', 'Fuel Oil NO. 6',
		'Fuel Oil', 'processed oil', 'Liquefied Petroleum Gas', 'Fuel Oil, Kerosene, Gasoline, Jet, Diesel', 'Fuel Grade Ethanol', 'Highly Volatile Liquid',
		'Refined Products', 'Empty Hazardous Liquid or Gas', 'Unleaded Gasoline','Propane','Naphtha','Isobutane','Ethylene','Propylene','EP Mix', 'EP Mix, Propane',
		'Ethylene Gas', 'Butadiene','Gas Oil', 'Diesel', 'Dilute Propylene', 'LPG, Distillates','Butyl Acrylate', 'Ammonia',
		'Chemical Grade Propylene', 'Benzene', 'C5 Raffinate, Butadiene','Carbon Black Oil','Butylene', 'Butane, Gasoline, EP Mix',
		'Pyrolysis Gasoline, Toluene Extract','Methanol','Distillate','Cyclohexane','Ethylbenzene','Butanol','Liquified Petroleum Gas','Pyrolysis Gasoline',
		'Ethylene Dichloride','Gasoline, Diesel, Fuel Oil, Kerosene','Propane, LPG','Gasoline, Diesel','Motor Fuels','Gasoline, Jet Fuel, Diesel','Ethane',
		'Benzene, Toluene','Monoethanolamine','Brine','Toluene, Benzene, Xylene','Ethyl Acrylate','Propylene Dilute','Anhydrous Ammonia',
		'Butane, Isobutane','Anhydrous Hcl','Propylene Polymer','Alkylate','Acetylene','Ethylene Glycol','Refined Products, LPG','Naphtha Lou Feed',
		'Styrene','Raffinate','Acetone','Diesel, Gasoline, Jet Fuel','Methyl Acetate','Gasoline, Distillates, Naphtha','Gasoline, Fuel Oil, Kerosene','Kerosene',
		'Acetic Acid','Acrylonitrile','Butane, Isobutane, Isobutylene','Lube Oil','Octene','Natural Gasoline, Feedstock','Triethanolamine','Petroleum/Mtbe',
		'Xylene','Ethane, Propane, Butane, Raw Plant','Toluene','Aniline Oil','Gasoline, Distillates','LPG, Distillates, Products','Vinyl Acetate Monomer','Cumene',
		'Propylene Glycol','Naphtha, Toluene','Refinery Grade Propylene','Vinyl Acetate','Hydrogen Peroxide',
		'Hexene','Acrylic Acid','Liquefied Propane Gas','Tertiary Butyl Alcohol','Dripolene','Rpg Polyethylene','Diesel, Distillate','Gasoline, Naphtha, Raffinate, Jet Fuel',
		'NGL','Aviation Gasoline','Petrochemicals','Isobutylene','Raffinate, Naphtha','Isobutane, Natural Gasoline','Magnaformate','Gasoline, Naphtha, Raffinate, Jet Fuel',
		'Decene','Raffinate, Butadiene','Gasoline, Fuel Oil','Diesel, Distillate','Propane,Ethane, Butane, Isobutane','Polymer Grade Propylene',
		'Petrochemicals','Non-HVL Products','Fuel Oil, Kerosene, Gasoline, Jet Fuel, Diesel','HVL Petrochemical','Bulk Oil','Liquified Sulphur','Empty Liq Nit Filled',
		'Oil Products','Butane, Jet Fuel, Propane, Refined Products','Petroleum Products','Diluent','Carbon Dioxide (Dense Phase)','#6 Oil, #4 Oil',
		'Other liquid','Y Grade','Propane Liquid, Liquid Natural Gas','Hazardous Liquids','Y-Grade'):
			node.fuelType = 'processed oil'
		elif node.fuelType in ('CRUDE OIL', 'Crude Oil','Crude','Condensate','Crude/Condensate', 'Converting to Crude', 'Crude Butadiene','Crude Oil/Condensate','Crude Oil Blends','Crude, Unknown Grade'):
			node.fuelType = 'crude oil'
		elif node.fuelType in (
		'LIGNITE COAL GAS (FROM COAL GASIFICATION)', 'WOOD GAS (FROM WOOD GASIFICATION)', 'ANTHRACITE',
		'GAS FROM REFUSE GASIFICATION',
		'GAS FROM BIOMASS GASIFICATION', 'COAL GAS (FROM COAL GASIFICATION)', 'GAS FROM FUEL OIL GASIFICATION',
		'BITUMINOUS COAL GAS (FROM COAL GASIFICATION)'):
			node.fuelType = 'syngas'
		elif node.fuelType in (
		'WASTE COAL', 'GOB', 'COAL (GENERIC)', 'LIGNITE', 'Coal', 'SUBBITUMINOUS', 'BITUMINOUS COAL'):
			node.fuelType = 'coal'
		elif node.fuelType in ('URANIUM', 'Uranium'):
			node.fuelType = 'uranium'
		elif node.fuelType in ('AGRICULTURAL WASTE', 'REFUSE', 'MANURE', 'BIOMASS', 'TIRES', 'POULTRY LITTER','Cat Feed'):
			node.fuelType = 'solid biomass feedstock'
		elif node.fuelType in (
		'WASTE WATER SLUDGE', 'DIGESTER GAS (SEWAGE SLUDGE GAS)', 'BIODIESEL', 'WASTE GAS', 'GEOTHERMAL STEAM',
		'WOOD WASTE LIQUIDS EXCL BLK LIQ (INCL RED LIQUOR,SLUDGE WOOD,SPENT SULFITE LIQUOR AND OTH LIQUIDS)'):
			node.fuelType = 'liquid biomass feedstock'
		elif node.fuelType in ('Water', 'Water Energy'):
			node.fuelType = 'water energy'
		elif node.fuelType in ('Solar', 'SOLAR'):
			node.fuelType = 'solar'
		elif node.fuelType in ('Wind', 'WIND'):
			node.fuelType = 'wind energy'
		elif node.fuelType in ('Other', 'WASTE HEAT', 'STEAM', 'UNKNOWN', 'COMPRESSED AIR', 'NOT APPLICABLE','Unknown', 'Oxygen', 'Carbon Dioxide', 'Carbon Monoxide',
		'MTBE', 'Carbon Dioxide - Sour','Ad Wash Oil','Salt Water','other','Coker Feed','Feedstock','CBLC','Firewater','Air','Polyethylene Water',
		'Toluene - Ethyl Benzene','Sulfur','Asphalt','Caustic','Slop Oil, Water','EPL','Reformate Udex Charge','Y Grade-Demethanized/Deethanized Product',
		'Empty','Test'):
			node.fuelType = 'other'
		else:
			print('Found a new fuel type that needs to be handled')
			print(node.fuelType)
			print('')
			fuels.add(node.fuelType)

		if node.fuelType not in self.refinements:
			self.refinements.append(node.fuelType)

		node.fuelType = [node.fuelType]

		return node, fuels

	def getPtsGPSRef(self):
		"""
		retreive all the X and Y coordinates of all buffers and line endpoints

		:param self: takes its own Oil grid object as an input
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
		retreive all the Oil grid nodes

		:param self: takes its own Oil grid object as an input
		:return: nodes: list of all buffer objects
		"""
		nodes = self.genC + self.OilTerminal + self.OilPorts + self.OilRefineries + self.OilIndBuffer
		return nodes

	def get_all_endpointsRef(self):
		"""
		retreive all the Oil grid line endpoints

		:param self: takes its own Oil grid object as an input
		:return: endpointsX: matrix of line origin and destination X coordinates of size lines*2 X refinements
		:return: endpointsY: matrix of line origin and destination X coordinates of size lines*2 X refinements
		"""
		endpointsX = sp.lil_matrix((len(self.OilCrudePipe) * 2 + len(self.OilRefPipe) * 2, len(self.refinements)))
		endpointsY = sp.lil_matrix((len(self.OilCrudePipe) * 2 + len(self.OilRefPipe) * 2, len(self.refinements)))
		for i, k1 in enumerate(self.OilCrudePipe):
			endpointsX[i * 2, self.refinements.index(k1.refinement[0])] = k1.fBus[0]
			endpointsY[i * 2, self.refinements.index(k1.refinement[0])] = k1.fBus[1]
			endpointsX[i * 2 + 1, self.refinements.index(k1.refinement[0])] = k1.tBus[0]
			endpointsY[i * 2 + 1, self.refinements.index(k1.refinement[0])] = k1.tBus[1]
		for j, k2 in enumerate(self.OilRefPipe):
			endpointsX[j * 2 + ((i+1) * 2), self.refinements.index(k2.refinement[0])] = k2.fBus[0]
			endpointsY[j * 2 + ((i+1) * 2), self.refinements.index(k2.refinement[0])] = k2.fBus[1]
			endpointsX[j * 2 + 1 + ((i+1) * 2), self.refinements.index(k2.refinement[0])] = k2.tBus[0]
			endpointsY[j * 2 + 1 + ((i+1) * 2), self.refinements.index(k2.refinement[0])] = k2.tBus[1]
		return endpointsX, endpointsY

