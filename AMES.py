#!/usr/bin/python3
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

import numpy as np
import geopandas as gpd
import pandas as pd

from shapely.geometry import Point
from shapely.geometry import shape

from ElectricGrid.ElectricGrid import ElectricGrid
from ElectricGrid.ElectricLine import ElectricLine
from ElectricGrid.Bus import Bus
from NGSystem.NGGrid import NGGrid
from NGSystem.NGPipe import NGPipe
from NGSystem.NGIndBuffer import NGIndBuffer
from OilSystem.OilGrid import OilGrid
from OilSystem.OilCrudePipe import OilCrudePipe
from OilSystem.OilRefPipe import OilRefPipe
from OilSystem.OilIndBuffer import OilIndBuffer
from CoalSystem.CoalGrid import CoalGrid
from CoalSystem.CoalIndBuffer import CoalIndBuffer
from CoalSystem.CoalRailroad import CoalRailroad
from SnapEdges2Grid import *

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
from collections import OrderedDict
import re
import time

class AMES(object):
	"""
	This class represents the physical AMES which contains the Electric grid, NG system,
	Oil system, and Coal system.  These are held as objects within the AMES which is
	used to clean and process each sub-system.

	Attributes:
		 ElecGrid			Electric Grid
		 NGSystem			NG System
		 oilSystem			Oil System
		 coalSystem			Coal System
		 nodes				List of all node objects in the AMES
		 lines				List of all line objects in the AMES
		 refinements		List of all refinements
	"""

	def __init__(self):
		"""
		This function initializes all of the AMES attributes.
		:return: Empty AMES object
		"""
		self.name = self.__class__.__name__
		self.elecGrid = None
		self.NGSystem = None
		self.oilSystem = None
		self.coalSystem = None
		self.nodes = np.array([None])
		self.lines = np.array([None])
		self.refinements = []
		self.regions = pd.DataFrame()
		self.controlAreas = None
		self.controllers = []

	def __repr__(self):
		"""
		This function is used to print your class attributes for easy visualization.
		:return: it returns the printed class with its attributes and values listed as a dictionary.

		>> This function is called as follows:
		>> print(self)
		"""
		from pprint import pformat
		return pformat(vars(self), indent=4, width=1)

	def initialize_regions(self, datafiles):
		"""
		Instantiate the regions by reading the regional shapes file. The
		resulting polygons are created here.

		:param datafiles: list of input file names
		:return:
		"""

		for file in datafiles:
			if 'States' in file:
				try:
					df = gpd.read_file(file)
					self.regions = df
				except:
					print('States file doesnt exist: ' + file)
					continue
			elif 'Control' in file or 'ISOs' in file:
				try:
					df = gpd.read_file(file)
					self.controlAreas = df
				except:
					print('Control Area file doesnt exist: ' + file)
					continue
			elif 'NG_Regions' in file:
				try:
					df = gpd.read_file(file)
					self.NGRegions = df
				except:
					print('NG Regions file doesnt exist: ' + file)
					continue
		return self

	def initialize_electric_grid(self, datafiles):
		"""
		Instantiate the electricGrid by reading all the individual resource files. The
		generators, buses, electricLine and loads are instantiated here.

		:param datafiles: list of input file names
		:return:
		"""

		self.elecGrid = ElectricGrid()

		self.elecGrid.initialize_electric_grid(datafiles)
		return self

	def initialize_NG_system(self, datafiles):
		"""
		Instantiate the NG system by reading all the individual resource files. The
		NG system resources are instantiated here.

		:param datafiles: list of input file names
		:return:
		"""

		self.NGSystem = NGGrid()

		self.NGSystem.initialize_NG_system(datafiles)

		return self

	def initialize_Oil_system(self, datafiles):
		"""
		Instantiate the Oil system by reading all the individual resource files. The
		oil power plant, terminal, oil pipelines, oil independent buffer, and oil refinery,
		and oil port are instantiated here.

		:param datafiles: list of input file names
		:return:
		"""

		self.oilSystem = OilGrid()

		self.oilSystem.initialize_Oil_system(datafiles)

		return self

	def initialize_Coal_system(self, datafiles):
		"""
		Instantiate the Coal system by reading all the individual resource files. The
		coal power plant, docks, sources, independent buffer, and Railroads are instantiated here.

		:param datafiles: list of input file names
		:return:
		"""

		self.coalSystem = CoalGrid()

		self.coalSystem.initialize_Coal_system(datafiles)

		return self

	def reviseAMES(self):
		"""
		Cluster and clean all buffers and endpoints in the AMES System.
		Add needed Lines and independent buffers to connect the system.
		Remove isolated buffers and lines from the system and join connected lines
		Set origin and destination names for all lines.

		:param self: Takes its own AMES object as an input
		:return: An updated AMES Object with cleaned data
		"""
		start_t = time.time()
		ptsBX, ptsBY, ptsODX, ptsODY = self.get_all_pointsRef()

		start_t = time.time()

		clusters, clustCenters, pts, ptsX, ptsY, resourcesToAdd = snapEdges2GridRef(ptsBX, ptsBY, ptsODX, ptsODY)

		end_t = time.time()
		print('total time taken for assigning clusters: %f' % (end_t - start_t))

		self.pull_all_nodes()
		self.pull_all_lines()

		clusters, pts, ptsX, ptsY = self.updateTransporters(resourcesToAdd, clusters, pts, ptsX, ptsY)

		ptsX, ptsY, pts, clusters = self.deleteIsoNodes(ptsX, ptsY, pts, clusters)

		self, clusters, resourceIdx = self.reviseCoords(clusters, pts, ptsX.row)

		clusters, resourceIdx = self.condenseClusterBuffers(clusters, resourceIdx)

		clusters, resourceIdx = self.joinLineSegs(clusters, resourceIdx)

		clusters, resourceIdx = self.addIndBuffers(clusters, clustCenters, resourceIdx)

		self.setNodeStates()

		self.setPipeODNames2(clusters, resourceIdx)

		end_t = time.time()
		print('total time taken in AMES: %f' % (end_t - start_t))

	def get_all_pointsRef(self):
		"""
		retreive all the X and Y coordinates of all buffers and line endpoints

		:param self: takes its own AMES object as an input
		:return: ptsBX: matrix of buffer X coordinates of size buffers X refinements
		:return: ptsBY: matrix of buffer Y coordinates of size buffers X refinements
		:return: ptsODX: matrix of line origin and destination X coordinates of size OD points X refinements
		:return: ptsODY: matrix of line origin and destination Y coordinates of size OD points X refinements
		"""
		print('Entering get_all_pointsRef')
		ptsBX = []
		ptsBY = []
		ptsODX = []
		ptsODY = []
		if self.elecGrid != None:
			ptsBElecX, ptsBElecY, ptsODElecX, ptsODElecY = self.elecGrid.getPtsGPSRef()
			for k1 in self.elecGrid.refinements:
				if k1 not in self.refinements:
					self.refinements.append(k1)

		if self.NGSystem != None:
			ptsBNGX, ptsBNGY, ptsODNGX, ptsODNGY = self.NGSystem.getPtsGPSRef()
			for k1 in self.NGSystem.refinements:
				if k1 not in self.refinements:
					self.refinements.append(k1)

		if self.oilSystem != None:
			ptsBoilX, ptsBoilY, ptsODoilX, ptsODoilY = self.oilSystem.getPtsGPSRef()
			for k1 in self.oilSystem.refinements:
				if k1 not in self.refinements:
					self.refinements.append(k1)

		if self.coalSystem != None:
			ptsBcoalX, ptsBcoalY, ptsODcoalX, ptsODcoalY = self.coalSystem.getPtsGPSRef()
			for k1 in self.coalSystem.refinements:
				if k1 not in self.refinements:
					self.refinements.append(k1)

		if self.elecGrid != None:
			tempBX = sp.lil_matrix((ptsBElecX.shape[0], len(self.refinements)))
			tempBY = sp.lil_matrix((ptsBElecX.shape[0], len(self.refinements)))
			tempODX = sp.lil_matrix((ptsODElecX.shape[0], len(self.refinements)))
			tempODY = sp.lil_matrix((ptsODElecX.shape[0], len(self.refinements)))
			for i, k1 in enumerate(self.elecGrid.refinements):
				tempBX[:, self.refinements.index(k1)] = ptsBElecX[:, i]
				tempBY[:, self.refinements.index(k1)] = ptsBElecY[:, i]
				tempODX[:, self.refinements.index(k1)] = ptsODElecX[:, i]
				tempODY[:, self.refinements.index(k1)] = ptsODElecY[:, i]

			ptsBX = sp.vstack((ptsBX, tempBX))
			ptsBY = sp.vstack((ptsBY, tempBY))
			ptsODX = sp.vstack((ptsODX, tempODX))
			ptsODY = sp.vstack((ptsODY, tempODY))

		if self.NGSystem != None:
			tempBX = sp.lil_matrix((ptsBNGX.shape[0], len(self.refinements)))
			tempBY = sp.lil_matrix((ptsBNGX.shape[0], len(self.refinements)))
			tempODX = sp.lil_matrix((ptsODNGX.shape[0], len(self.refinements)))
			tempODY = sp.lil_matrix((ptsODNGX.shape[0], len(self.refinements)))
			for i, k1 in enumerate(self.NGSystem.refinements):
				tempBX[:, self.refinements.index(k1)] = ptsBNGX[:, i]
				tempBY[:, self.refinements.index(k1)] = ptsBNGY[:, i]
				tempODX[:, self.refinements.index(k1)] = ptsODNGX[:, i]
				tempODY[:, self.refinements.index(k1)] = ptsODNGY[:, i]
			ptsBX = sp.vstack((ptsBX, tempBX))
			ptsBY = sp.vstack((ptsBY, tempBY))
			ptsODX = sp.vstack((ptsODX, tempODX))
			ptsODY = sp.vstack((ptsODY, tempODY))

		if self.oilSystem != None:
			tempBX = sp.lil_matrix((ptsBoilX.shape[0], len(self.refinements)))
			tempBY = sp.lil_matrix((ptsBoilX.shape[0], len(self.refinements)))
			tempODX = sp.lil_matrix((ptsODoilX.shape[0], len(self.refinements)))
			tempODY = sp.lil_matrix((ptsODoilX.shape[0], len(self.refinements)))
			for i, k1 in enumerate(self.oilSystem.refinements):
				tempBX[:, self.refinements.index(k1)] = ptsBoilX[:, i]
				tempBY[:, self.refinements.index(k1)] = ptsBoilY[:, i]
				tempODX[:, self.refinements.index(k1)] = ptsODoilX[:, i]
				tempODY[:, self.refinements.index(k1)] = ptsODoilY[:, i]
			ptsBX = sp.vstack((ptsBX, tempBX))
			ptsBY = sp.vstack((ptsBY, tempBY))
			ptsODX = sp.vstack((ptsODX, tempODX))
			ptsODY = sp.vstack((ptsODY, tempODY))

		if self.coalSystem != None:
			tempBX = sp.lil_matrix((ptsBcoalX.shape[0], len(self.refinements)))
			tempBY = sp.lil_matrix((ptsBcoalX.shape[0], len(self.refinements)))
			tempODX = sp.lil_matrix((ptsODcoalX.shape[0], len(self.refinements)))
			tempODY = sp.lil_matrix((ptsODcoalX.shape[0], len(self.refinements)))
			for i, k1 in enumerate(self.coalSystem.refinements):
				tempBX[:, self.refinements.index(k1)] = ptsBcoalX[:, i]
				tempBY[:, self.refinements.index(k1)] = ptsBcoalY[:, i]
				tempODX[:, self.refinements.index(k1)] = ptsODcoalX[:, i]
				tempODY[:, self.refinements.index(k1)] = ptsODcoalY[:, i]
			ptsBX = sp.vstack((ptsBX, tempBX))
			ptsBY = sp.vstack((ptsBY, tempBY))
			ptsODX = sp.vstack((ptsODX, tempODX))
			ptsODY = sp.vstack((ptsODY, tempODY))

		ptsBX.row = ptsBX.row - 1
		ptsBY.row = ptsBY.row - 1
		ptsBX._shape = (ptsBX._shape[0] - 1, ptsBX._shape[1])
		ptsBY._shape = (ptsBY._shape[0] - 1, ptsBY._shape[1])
		ptsODX.row = ptsODX.row - 1
		ptsODY.row = ptsODY.row - 1
		ptsODX._shape = (ptsODX._shape[0] - 1, ptsODX._shape[1])
		ptsODY._shape = (ptsODY._shape[0] - 1, ptsODY._shape[1])

		return ptsBX, ptsBY, ptsODX, ptsODY

	def pull_all_nodes(self):
		"""
		Pulls all the nodes form the ElecGrid, NGGrid, OilGrid, and CoalGrid objects into the nodes attribute.
		This consolidates all nodes from each subsystem into a single AMES list

		:param self: Takes its own AMES object as an input
		:return: An updated AMES Object with a populated nodes attribute
		"""
		print('Pulling all nodes')
		if self.elecGrid != None:
			self.nodes = np.hstack((self.nodes, self.elecGrid.get_all_nodes()))

		if self.NGSystem != None:
			self.nodes = np.hstack((self.nodes, self.NGSystem.get_all_nodes()))

		if self.oilSystem != None:
			self.nodes = np.hstack((self.nodes, self.oilSystem.get_all_nodes()))

		if self.coalSystem != None:
			self.nodes = np.hstack((self.nodes, self.coalSystem.get_all_nodes()))

		self.nodes = np.delete(self.nodes, [0], 0)
		return self.nodes

	def pull_all_lines(self):
		"""
		Pulls all the lines form the ElecGrid, NGGrid, OilGrid, and CoalGrid objects into the lines attribute.
		This consolidates all nodes from each subsystem into a single AMES list

		:param self: Takes its own AMES object as an input
		:return: An updated AMES Object with a populated lines attribute
		"""
		print('Pulling all lines')
		if self.elecGrid != None:
			self.lines = np.hstack((self.lines, self.elecGrid.electricLine))

		if self.NGSystem != None:
			self.lines = np.hstack((self.lines, self.NGSystem.NGPipe))

		if self.oilSystem != None:
			self.lines = np.hstack((self.lines, self.oilSystem.OilCrudePipe))
			self.lines = np.hstack((self.lines, self.oilSystem.OilRefPipe))

		if self.coalSystem != None:
			self.lines = np.hstack((self.lines, self.coalSystem.CoalRailroad))

		self.lines = np.delete(self.lines, [0], 0)
		return self.lines

	def updateTransporters(self, resourcesToAdd, clusters, pts, ptsX, ptsY):
		"""
		Creates and adds lines to the AMES object as designated by the resourcesToAdd paramater.

		:param: resourcesToAdd: a list of lines that need to be added to the AMES designated by Origin and Destination
		:param: clusters: A list of size # of points, designating each points cluster
		:param: pts: a list of GPS coords for each buffer and endpoint in the AMES
		:param: ptsX: matrix of X coordinates of size points X refinements
		:param: ptsY: matrix of Y coordinates of size points X refinements
		:return: clusters: An updated list of size # of points, designating each points cluster
		:return: pts: An updated list of GPS coords for each buffer and endpoint in the AMES
		:return: ptsX: An updated matrix of X coordinates of size points X refinements
		:return: ptsY: An updated matrix of Y coordinates of size points X refinements
		"""
		print('Entering updateTransporters')
		# Preallocate lists and counters
		lines = []
		clust = []
		gps = []
		rows = []
		cols = []
		dataX = []
		dataY = []
		count = 0
		transmission_count = 0
		NG_count = 0
		oilRef_count = 0
		oilCrude_count = 0
		coal_count = 0
		other_count = 0

		# create new line to add based on refinement
		for i, k1 in enumerate(resourcesToAdd):
			ref = self.refinements[ptsX.col[k1[1]]]
			if ref == 'electric power at 132kV':
				transmission_count += 1
				new_instance = ElectricLine()
				if self.elecGrid != None:
					new_instance.lineName = 'Transmission Line ' + str(
						len(self.elecGrid.electricLine) + transmission_count)
				else:
					new_instance.lineName = 'Transmission Line ' + str(transmission_count)
				new_instance.refinement = [ref]
				new_instance.fuelType = [ref]
				new_instance.attrib_ref = [ref]
				new_instance.type = 'ElecLine'
			elif ref == 'processed gas' or ref == 'syngas' or ref == 'raw gas':
				NG_count += 1
				new_instance = NGPipe()
				if self.NGSystem != None:
					new_instance.lineName = 'NG Pipeline ' + str(len(self.NGSystem.NGPipe) + NG_count)
				else:
					new_instance.lineName = 'NG Pipeline ' + str(NG_count)
				new_instance.refinement = [ref]
				new_instance.fuelType = [ref]
				new_instance.attrib_ref = [ref]
				new_instance.type = 'NGPipe'
			elif ref == 'processed oil':
				oilRef_count += 1
				new_instance = OilRefPipe()
				if self.oilSystem != None:
					new_instance.lineName = 'OilR Pipeline ' + str(len(self.oilSystem.OilRefPipe) + oilRef_count)
				else:
					new_instance.lineName = 'OilR Pipeline ' + str(oilRef_count)
				new_instance.refinement = [ref]
				new_instance.fuelType = [ref]
				new_instance.attrib_ref = [ref]
				new_instance.type = 'oilRPipe'
			elif ref == 'crude oil' or ref == 'liquid biomass feedstock' or ref == 'water energy':
				oilCrude_count += 1
				new_instance = OilCrudePipe()
				if self.oilSystem != None:
					new_instance.lineName = 'OilC Pipeline ' + str(len(self.oilSystem.OilCrudePipe) + oilCrude_count)
				else:
					new_instance.lineName = 'OilC Pipeline ' + str(oilCrude_count)
				new_instance.refinement = [ref]
				new_instance.fuelType = [ref]
				new_instance.attrib_ref = [ref]
				new_instance.type = 'oilCrudePipe'
			elif ref == 'coal':
				coal_count += 1
				new_instance = CoalRailroad()
				if self.coalSystem != None:
					new_instance.lineName = 'coal railroad ' + str(len(self.coalSystem.CoalRailroad) + coal_count)
				else:
					new_instance.lineName = 'coal railroad ' + str(coal_count)
				new_instance.refinement = [ref]
				new_instance.fuelType = [ref]
				new_instance.attrib_ref = [ref]
				new_instance.type = 'railroad'
			elif ref == 'other' or ref == 'solid biomass feedstock' or ref == 'uranium':
				other_count += 1
				new_instance = OilCrudePipe()
				new_instance.lineName = 'Other Pipeline ' + str(other_count)
				new_instance.refinement = [ref]
				new_instance.fuelType = [ref]
				new_instance.attrib_ref = [ref]
				new_instance.type = 'otherPipe'
			else:
				print('\nunhandled refinement in update transporters')
				print(ref)

			# Set added line origin and destination
			new_instance.fBus = (ptsX.data[k1[1]], ptsY.data[k1[1]])
			new_instance.tBus = (ptsX.data[k1[0]], ptsY.data[k1[0]])
			new_instance.fBus_gps = (ptsX.data[k1[1]], ptsY.data[k1[1]])
			new_instance.tBus_gps = (ptsX.data[k1[0]], ptsY.data[k1[0]])
			new_instance.status = 'true'
			new_instance.clust_origin = clusters[k1[1]]
			new_instance.clust_dest = clusters[k1[0]]
			new_instance.attrib_origin = new_instance.fBus
			new_instance.attrib_dest = new_instance.tBus

			# Append to list of newly added lines
			clust.append(new_instance.clust_origin)
			clust.append(new_instance.clust_dest)
			gps.append(new_instance.attrib_origin)
			gps.append(new_instance.attrib_dest)
			lines.append(new_instance)
			rows.append(i * 2 + (len(self.lines) * 2))
			rows.append(i * 2 + 1 + (len(self.lines) * 2))
			cols.append(ptsX.col[k1[1]])
			cols.append(ptsX.col[k1[1]])
			dataX.append(ptsX.data[k1[1]])
			dataX.append(ptsX.data[k1[0]])
			dataY.append(ptsY.data[k1[1]])
			dataY.append(ptsY.data[k1[0]])
			count += 1

		if len(self.lines) > 0 and count > 0:  # If existing lines and lines to add
			linePoints = np.where(ptsX.row == len(self.lines) * 2)[0][0]
			clusters = np.insert(clusters, linePoints, clust)
			pts = np.insert(pts, linePoints, gps, axis=0)
			ptsX.row[linePoints:] = ptsX.row[linePoints:] + len(rows)
			ptsX.row = np.insert(ptsX.row, linePoints, rows)
			ptsX.col = np.insert(ptsX.col, linePoints, cols)
			ptsX.data = np.insert(ptsX.data, linePoints, dataX)
			ptsX._shape = (ptsX._shape[0] + len(rows), ptsX._shape[1])

			ptsY.row[linePoints:] = ptsY.row[linePoints:] + len(rows)
			ptsY.row = np.insert(ptsY.row, linePoints, rows)
			ptsY.col = np.insert(ptsY.col, linePoints, cols)
			ptsY.data = np.insert(ptsY.data, linePoints, dataY)
			ptsY._shape = (ptsY._shape[0] + len(rows), ptsY._shape[1])
		self.lines = np.hstack((self.lines, lines))

		return clusters, pts, ptsX, ptsY

	def deleteIsoNodes(self, ptsX, ptsY, pts, clusters):
		"""
		Delets all isolated nodes from the AMES object

		:param: clusters: A list of size # of points, designating each points cluster
		:param: pts: a list of GPS coords for each buffer and endpoint in the AMES
		:param: ptsX: matrix of X coordinates of size points X refinements
		:param: ptsY: matrix of Y coordinates of size points X refinements
		:return: clusters: An updated list of size # of points, designating each points cluster
		:return: pts: An updated list of GPS coords for each buffer and endpoint in the AMES
		:return: ptsX: An updated matrix of X coordinates of size points X refinements
		:return: ptsY: An updated matrix of Y coordinates of size points X refinements
		"""
		print('Entering deleteIsoNodes')
		isoPoints = np.where(np.equal(clusters, None))[0]
		isoResourcePoints = np.flip(pd.unique(ptsX.row[isoPoints]))
		count = 0
		for k1 in isoResourcePoints:
			connected = False
			isoPoint = np.flip(np.where(ptsX.row == k1)[0])
			for k2 in isoPoint:
				if clusters[k2] != None:
					connected = True
					continue
				clusters = np.delete(clusters, k2)
				pts = np.delete(pts, k2, axis=0)

				ptsX.row = np.delete(ptsX.row, k2, 0)
				ptsX.col = np.delete(ptsX.col, k2, 0)
				ptsX.data = np.delete(ptsX.data, k2, 0)

				ptsY.row = np.delete(ptsY.row, k2, 0)
				ptsY.col = np.delete(ptsY.col, k2, 0)
				ptsY.data = np.delete(ptsY.data, k2, 0)
			if connected:
				continue
				print('not isolated')
			elif k2 < len(ptsX.row):
				ptsX.row[k2:] = ptsX.row[k2:] - 1
				ptsY.row[k2:] = ptsY.row[k2:] - 1
			count += 1
			self.nodes = np.delete(self.nodes, k1 - len(self.lines) * 2)
			ptsX._shape = (ptsX._shape[0] - 1, ptsX._shape[1])
			ptsY._shape = (ptsY._shape[0] - 1, ptsY._shape[1])
		print('deleted isolated nodes: %d' % count)

		return ptsX, ptsY, pts, clusters

	def reviseCoords(self, clusters, pts, resourceIdx):
		"""
		Sets the clusters of all point in the AMES

		:param: clusters: A list of size # of points, designating each points cluster
		:param: pts: a list of GPS coords for each buffer and endpoint in the AMES
		:param: resourceIdx: a list of length pts that designates each points resource
		:return: clusters: An updated list of size # of points, designating each points cluster
		:return: resourceIdx: An updated list of length pts that designates each points resource
		"""
		print('In reviseCoords')
		del_lines = []
		del_buffers = []

		# set pipe and buffer coords to match pts coords (cluster midpoints)
		numEndpoints = len(self.lines) * 2
		countB = 0
		countO = 0
		isoCount = 0
		for k1 in range(len(pts)):
			if resourceIdx[k1] >= numEndpoints:  # Buffer
				countB += 1
				pt = self.nodes[resourceIdx[k1] - numEndpoints]
				if pt.cluster == None:
					pt.cluster = [clusters[k1]]
				else:
					pt.cluster.append(clusters[k1])
				pt.gpsX = pts[k1][0]
				pt.gpsY = pts[k1][1]
			elif resourceIdx[k1] % 2 == 0:  # Line Origin
				countO += 1
				pt = self.lines[int(np.floor(resourceIdx[k1] / 2))]
				pt.attrib_origin = pts[k1]
				pt.clust_origin = clusters[k1]
				self.lines[int(np.floor(resourceIdx[k1] / 2))] = pt
			elif resourceIdx[k1] % 2 != 0:  # Line Destination
				pt = self.lines[int(np.floor(resourceIdx[k1] / 2))]
				pt.attrib_dest = pts[k1]
				pt.clust_dest = clusters[k1]
				self.lines[int(np.floor(resourceIdx[k1] / 2))] = pt
				if pt.clust_origin == pt.clust_dest:
					del_lines.append(int(np.floor(resourceIdx[k1] / 2)))
			else:
				print('Error matching points with resources.')

		for k2 in np.flip(del_lines):  # remove self looping lines
			clust = self.lines[k2].clust_origin
			idxRemove = [k2*2+1,k2*2]
			self.lines = np.delete(self.lines, k2)
			clusters = np.delete(clusters, idxRemove)
			resourceIdx = np.delete(resourceIdx, idxRemove)
			resourceIdx[idxRemove[1]:] = resourceIdx[idxRemove[1]:]-2
			temp = np.where(clusters == clust)[0]
			if any(temp<len(self.lines)*2):
				continue
			else:
				for k3 in temp:
					del_buffers.append(resourceIdx[k3]-len(self.lines)*2)

		del_buffers = np.unique(del_buffers)
		for k3 in np.flip(del_buffers):  # Remove new isolated buffers
			self.nodes = np.delete(self.nodes, k3)
			temp1 = np.where(resourceIdx == k3 + len(self.lines)*2)[0]
			clusters = np.delete(clusters, temp1)
			resourceIdx = np.delete(resourceIdx, temp1)
			resourceIdx[temp1[0]:] = resourceIdx[temp1[0]:] - 1

		print('Deleted {} self looping lines'.format(len(del_lines)))
		print('Deleted {} isolated nodes post self looping lines'.format(len(del_buffers)))
		return self, clusters, resourceIdx

	def condenseClusterBuffers(self, clusters, resourceIdx):
		print('Condensing overlapping like nodes')

		uniClusts = np.unique(clusters)
		for k1 in uniClusts:
			foundClust = np.where(clusters == k1)[0]
			resources = resourceIdx[foundClust]
			resources = resources[resources >= len(self.lines) * 2]
			if len(resources) > 1:
				nodeTypes = []
				nodeIdxs = []
				duplicates = []
				for k2 in resources:
					nodeIdx = k2 - (len(self.lines) * 2)
					currentNode = self.nodes[nodeIdx]
					if currentNode.nodeType not in nodeTypes:
						nodeTypes.append(currentNode.nodeType)
						nodeIdxs.append(nodeIdx)
					else:
						temp = nodeTypes.index(currentNode.nodeType)
						primeNode = self.nodes[nodeIdxs[temp]]
						if primeNode.nodeType == 'GenC' or primeNode.nodeType == 'GenS':
							duplicate = False
							for k3, fuel in enumerate(primeNode.fuelType):
								if fuel == currentNode.fuelType[0] and primeNode.cap[k3] == currentNode.cap[0]:
									duplicate = True
									break
							if not duplicate:
								primeNode.fuelType = primeNode.fuelType + currentNode.fuelType
								primeNode.cap = primeNode.cap + currentNode.cap
							duplicates.append(nodeIdx)
						elif primeNode.nodeType == 'LoadC' or primeNode.nodeType == 'LoadS':
							duplicates.append(nodeIdx)
						elif primeNode.nodeType == 'NGProcessor':
							duplicates.append(nodeIdx)
						elif primeNode.nodeType == 'NGReceiptDelivery':
							duplicates.append(nodeIdx)

						else:
							duplicates.append(nodeIdx)
						primeNode.cluster = list(pd.unique(primeNode.cluster + currentNode.cluster))

				if len(duplicates) > 0:
					for k3 in np.flip(duplicates):
						temp = np.flip(np.where(resourceIdx == k3 + (len(self.lines) * 2))[0])
						clusters = np.delete(clusters, temp)
						resourceIdx = np.delete(resourceIdx, temp)
						self.nodes = np.delete(self.nodes, k3)
						resourceIdx[temp[-1]:] = resourceIdx[temp[-1]:] - 1
		return clusters, resourceIdx

	def condenseBuffers(self, clusters, resourceIdx):
		print('Condensing overlapping like nodes')
		uniClusts = np.unique(clusters)
		for k1 in uniClusts:
			foundClust = np.where(clusters == k1)[0]
			resources = resourceIdx[foundClust]
			resources = resources[resources>=len(self.lines)*2]
			if len(resources)>1:
				nodeTypes = []
				nodeIdxs = []
				clustersToAppend = []
				primeResourceIdx = []
				duplicates = []
				for k2 in resources:
					nodeIdx = k2-(len(self.lines)*2)
					if self.nodes[nodeIdx].nodeType not in nodeTypes:
						nodeTypes.append(self.nodes[nodeIdx].nodeType)
						nodeIdxs.append(nodeIdx)
					else:
						temp = nodeTypes.index(self.nodes[nodeIdx].nodeType)
						primeNode = self.nodes[nodeIdxs[temp]]
						if hasattr(primeNode, 'fuelType'):
							if primeNode.fuelType != None:
								primeNode.fuelType = list(pd.unique(primeNode.fuelType+self.nodes[nodeIdx].fuelType))
						if hasattr(primeNode, 'cap'):
							primeNode.cap = primeNode.cap + self.nodes[nodeIdx].cap
							primeNode.cap = primeNode.cap[:len(primeNode.fuelType)]
						if hasattr(primeNode, 'attrib_ref'):
							primeNode.attrib_ref = list(pd.unique(primeNode.attrib_ref + self.nodes[nodeIdx].attrib_ref))
						if hasattr(primeNode, 'refinement'):
							primeNode.refinement = list(pd.unique(primeNode.refinement + self.nodes[nodeIdx].refinement))
						newClusts = list(set(self.nodes[nodeIdx].cluster)-set(primeNode.cluster))
						if len(newClusts) > 0:
							primeNode.cluster = primeNode.cluster + newClusts
							clustersToAppend = clustersToAppend + [newClusts]
							primeResourceIdx = primeResourceIdx + [nodeIdxs[temp]]
						if nodeIdx not in duplicates:
							duplicates.append(nodeIdx)
				if len(duplicates) > 0:
					for k3 in np.flip(duplicates):
						temp = np.flip(np.where(resourceIdx == k3+(len(self.lines)*2))[0])
						clusters = np.delete(clusters, temp)
						resourceIdx = np.delete(resourceIdx, temp)
						self.nodes = np.delete(self.nodes, k3)
						resourceIdx[temp[-1]:] = resourceIdx[temp[-1]:] - 1

				if len(clustersToAppend) > 0:
					for k4 in range(len(clustersToAppend)):
						temp = np.flip(np.where(resourceIdx == primeResourceIdx[k4]+(len(self.lines)*2))[0])[0]
						for k5 in clustersToAppend[k4]:
							np.insert(clusters, temp, k5)
							np.insert(resourceIdx, temp, primeResourceIdx[k4]+(len(self.lines)*2))
		return clusters, resourceIdx

	def joinLineSegs(self, clusters, resourceIdx):
		"""
		Join all lines that share endpoints with exactly one other line and no buffers

		:param: clusters: A list of size # of points, designating each points cluster
		:param: resourceIdx: a list of length pts that designates each points resource
		:return: clusters: An updated list of size # of points, designating each points cluster
		:return: resourceIdx: An updated list of length pts that designates each points resource
		"""
		print('In joinLineSegs')
		joined = 0
		k1 = 0
		while k1 < len(self.lines):
			pipe1 = self.lines[k1]
			clust = np.where(clusters == pipe1.clust_origin)[0]  # clusters that match the origin
			resources = np.unique(resourceIdx[clust])
			if len(resources) == 2:
				if all(resources < len(self.lines) * 2):
					idxPipe2 = int(np.floor(resources[np.where(k1 * 2 != resources)[0]] / 2))
					pipe2 = self.lines[idxPipe2]
					if pipe1.clust_origin == pipe2.clust_dest and not pipe1.clust_dest == pipe2.clust_origin:  # origin 2 dest
						pipe1.clust_origin = pipe2.clust_origin
						pipe1.attrib_origin = pipe2.attrib_origin
					elif pipe1.clust_origin == pipe2.clust_origin and not pipe1.clust_dest == pipe2.clust_dest:  # origin to origin
						pipe1.clust_origin = pipe2.clust_dest
						pipe1.attrib_origin = pipe2.attrib_dest
					else:  # looping lines
						k1 += 1
						continue
					clusters[np.where(resourceIdx == k1 * 2)[0]] = pipe1.clust_origin
					idx2Del1 = np.where(resourceIdx == idxPipe2 * 2)[0]
					clusters = np.delete(clusters, idx2Del1)
					resourceIdx = np.delete(resourceIdx, idx2Del1)
					idx2Del2 = np.where(resourceIdx == idxPipe2 * 2 + 1)[0]
					clusters = np.delete(clusters, idx2Del2)
					resourceIdx = np.delete(resourceIdx, idx2Del2)
					if idxPipe2 * 2 + 1 < max(resourceIdx):
						idx = np.where(resourceIdx == (idxPipe2 + 1) * 2)[0][0]
						resourceIdx[idx:] = resourceIdx[idx:] - 2
					self.lines[k1] = pipe1
					self.lines = np.delete(self.lines, idxPipe2)
					joined += 1
					continue

			clust = np.where(clusters == pipe1.clust_dest)[0]  # clusters that match the destination
			resources = np.unique(resourceIdx[clust])
			if len(resources) == 2:
				if all(resources < len(self.lines) * 2):
					idxPipe2 = int(np.floor(resources[np.where(k1 * 2 + 1 != resources)[0]] / 2))
					pipe2 = self.lines[idxPipe2]
					if pipe1.clust_dest == pipe2.clust_dest and not pipe1.clust_origin == pipe2.clust_origin:  # dest to dest
						pipe1.clust_dest = pipe2.clust_origin
						pipe1.attrib_dest = pipe2.attrib_origin
					elif pipe1.clust_dest == pipe2.clust_origin and not pipe1.clust_origin == pipe2.clust_dest:  # dest to origin
						pipe1.clust_dest = pipe2.clust_dest
						pipe1.attrib_dest = pipe2.attrib_dest
					else:  # looping lines
						k1 += 1
						continue
					clusters[np.where(resourceIdx == k1 * 2 + 1)[0]] = pipe1.clust_dest
					idx2Del1 = np.where(resourceIdx == idxPipe2 * 2)[0]
					clusters = np.delete(clusters, idx2Del1)
					resourceIdx = np.delete(resourceIdx, idx2Del1)
					idx2Del2 = np.where(resourceIdx == idxPipe2 * 2 + 1)[0]
					clusters = np.delete(clusters, idx2Del2)
					resourceIdx = np.delete(resourceIdx, idx2Del2)
					if idxPipe2 * 2 + 1 < max(resourceIdx):
						idx = np.where(resourceIdx == (idxPipe2 + 1) * 2)[0][0]
						resourceIdx[idx:] = resourceIdx[idx:] - 2
					self.lines[k1] = pipe1
					self.lines = np.delete(self.lines, idxPipe2)
					joined += 1
					continue

			k1 += 1
		print('joined lines: %d' % joined)
		return clusters, resourceIdx

	def addIndBuffers(self, clusters, clustCenters, resourceIdx):
		"""
		Add independent buffers where 3+ lines meet without a buffer.
		:param: clusters: A list of size # of points, designating each points cluster
		:param: clustCenters: A list of size # of clusters, designating each clusters center GPS
		:param: resourceIdx: a list of length pts that designates each points resource
		:return: clusters: An updated list of size # of points, designating each points cluster
		:return: resourceIdx: An updated list of length pts that designates each points resource
		"""
		print('Entering addIndBuffers')
		# if cluster members > 2 and no buffer already in cluster add independent buffer at cluster midpoint
		count = 0
		buffers = []
		expanded_clusts = []
		expanded_buffers = []
		clustsU, returnIDX = np.unique(clusters, return_index=True)
		for k1 in range(len(clustsU)):
			clust = np.where(clusters == clustsU[k1])[0]
			resources = np.unique(resourceIdx[clust])
			if any(resources >= len(self.lines) * 2):  # if any clusters have nodes
				continue
			refinements = []
			for k2 in resources:
				idxPipe = int(np.floor(k2 / 2))
				refinements.extend(self.lines[idxPipe].refinement)
			refinements = np.unique(refinements)

			if 'electric power at 132kV' in refinements:
				new_instance = Bus()
				new_instance.gpsX = clustCenters[k1][0]
				new_instance.gpsY = clustCenters[k1][1]
				new_instance.nodeName = 'IndBuffer ' + str(count)
				new_instance.busName = 'IndBuffer ' + str(count)
				new_instance.cluster = [clustsU[k1]]
				new_instance.type = 'buffer'
				new_instance.status = 'true'
				new_instance.attrib_ref = refinements
				buffers.append(new_instance)
				expanded_clusts.append(clustsU[k1])
				expanded_buffers.append(max(resourceIdx) + count + 1)
				count += 1
			elif 'processed gas' in refinements or 'syngas' in refinements or 'raw gas' in refinements:
				new_instance = NGIndBuffer()
				new_instance.gpsX = clustCenters[k1][0]
				new_instance.gpsY = clustCenters[k1][1]
				new_instance.nodeName = 'IndBuffer ' + str(count)
				new_instance.busName = 'IndBuffer ' + str(count)
				new_instance.cluster = [clustsU[k1]]
				new_instance.type = 'buffer'
				new_instance.status = 'true'
				new_instance.attrib_ref = refinements
				buffers.append(new_instance)
				expanded_clusts.append(clustsU[k1])
				expanded_buffers.append(max(resourceIdx) + count + 1)
				count += 1
			elif 'processed oil' in refinements or 'crude oil' in refinements or 'liquid biomass feedstock' in refinements or 'water energy' in refinements:
				new_instance = OilIndBuffer()
				new_instance.gpsX = clustCenters[k1][0]
				new_instance.gpsY = clustCenters[k1][1]
				new_instance.nodeName = 'IndBuffer ' + str(count)
				new_instance.busName = 'IndBuffer ' + str(count)
				new_instance.cluster = [clustsU[k1]]
				new_instance.type = 'buffer'
				new_instance.status = 'true'
				new_instance.attrib_ref = refinements
				buffers.append(new_instance)
				expanded_clusts.append(clustsU[k1])
				expanded_buffers.append(max(resourceIdx) + count + 1)
				count += 1
			elif 'solid biomass feedstock' in refinements:
				new_instance = OilIndBuffer()
				new_instance.gpsX = clustCenters[k1][0]
				new_instance.gpsY = clustCenters[k1][1]
				new_instance.nodeName = 'IndBuffer ' + str(count)
				new_instance.busName = 'IndBuffer ' + str(count)
				new_instance.cluster = [clustsU[k1]]
				new_instance.type = 'buffer'
				new_instance.status = 'true'
				new_instance.attrib_ref = refinements
				buffers.append(new_instance)
				expanded_clusts.append(clustsU[k1])
				expanded_buffers.append(max(resourceIdx) + count + 1)
				count += 1
			elif 'coal' in refinements:
				new_instance = CoalIndBuffer()
				new_instance.gpsX = clustCenters[k1][0]
				new_instance.gpsY = clustCenters[k1][1]
				new_instance.nodeName = 'IndBuffer ' + str(count)
				new_instance.busName = 'IndBuffer ' + str(count)
				new_instance.cluster = [clustsU[k1]]
				new_instance.type = 'buffer'
				new_instance.status = 'true'
				new_instance.attrib_ref = refinements
				buffers.append(new_instance)
				expanded_clusts.append(clustsU[k1])
				expanded_buffers.append(max(resourceIdx) + count + 1)
				count += 1
			elif 'other' in refinements:
				new_instance = Bus()
				new_instance.gpsX = clustCenters[k1][0]
				new_instance.gpsY = clustCenters[k1][1]
				new_instance.nodeName = 'IndBuffer ' + str(count)
				new_instance.busName = 'IndBuffer ' + str(count)
				new_instance.cluster = [clustsU[k1]]
				new_instance.type = 'buffer'
				new_instance.status = 'true'
				new_instance.attrib_ref = refinements
				buffers.append(new_instance)
				expanded_clusts.append(clustsU[k1])
				expanded_buffers.append(max(resourceIdx) + count + 1)
				count += 1
			else:
				print('Unhandled refinements in addIndBuffer')
				print(refinements)
				print(resources)
				print('')

		self.nodes = np.hstack((self.nodes, buffers))
		expanded_clusts = np.array(expanded_clusts)
		clusters = np.concatenate((clusters, expanded_clusts))
		expanded_buffers = np.array(expanded_buffers)
		resourceIdx = np.concatenate((resourceIdx, expanded_buffers))

		return clusters, resourceIdx

	def setPipeODNames(self):
		"""
		Set the origins and destinations of all lines to the names of the buffers at the endpoints

		:param: self: This takes itself in to set the endpoints
		:return:
		"""
		print('In setPipeODNames')
		count = 0
		verts = self.nodes
		pipes = self.lines
		delLine = []
		for i, k1 in enumerate(pipes):
			o = False
			d = False
			k1.controller = []
			for j, k2 in enumerate(verts):
				if k1.clust_origin in k2.cluster and k2.nodeName not in k1.tBus:
					if type(k1.fBus) == tuple:
						k1.fBus = [k2.nodeName]
					else:
						k1.fBus.append(k2.nodeName)
					o = True
					for controller in k2.controller:
						if controller not in k1.controller:
							k1.controller.append(controller)
				if k1.clust_dest in k2.cluster and k2.nodeName not in k1.fBus:
					if type(k1.tBus) == tuple:
						k1.tBus = [k2.nodeName]
					else:
						k1.tBus.append(k2.nodeName)
					d = True
					for controller in k2.controller:
						if controller not in k1.controller:
							k1.controller.append(controller)
			if not o or not d:
				if not o:
					print('origin false')
				if not d:
					print('destination false')
				count += 1
				delLine.append(i)
		for k3 in np.flip(delLine):
			self.lines = np.delete(self.lines, k3)

	def findClusterPrimary(self, lineType, nodeIdxs):
		nodes = self.nodes[nodeIdxs]
		primaryNode = None
		primaryNodeType = None
		primaryNodeIdx = None
		if lineType == 'ElecLine':
			for k1 in range(len(nodes)):
				node = nodes[k1]
				if node.nodeType == 'LoadC':
					primaryNode = node
					primaryNodeIdx = nodeIdxs[k1]
					break
				elif node.nodeType == 'LoadS':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
				elif node.nodeType == 'GenC' and primaryNodeType != 'LoadS':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
				elif node.nodeType == 'GenS'and primaryNodeType != 'LoadS' and primaryNodeType != 'GenC':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
		elif lineType == 'NGPipe':
			for k1 in range(len(nodes)):
				node = nodes[k1]
				if node.nodeType == 'NGReceiptDelivery':
					primaryNode = node
					primaryNodeIdx = nodeIdxs[k1]
					break
				elif node.nodeType == 'NGProcessor':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
				elif node.nodeType == 'compressor'and primaryNodeType != 'NGProcessor':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
				else:
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
		elif lineType == 'OilRefPipe':
			for k1 in range(len(nodes)):
				node = nodes[k1]
				if node.nodeType == 'OilPort':
					primaryNode = node
					primaryNodeIdx = nodeIdxs[k1]
					break
				elif node.nodeType == 'OilTerminal':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
				elif node.nodeType == 'OilRefinery' and primaryNodeType != 'OilTerminal':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
		elif lineType == 'OilCrudePipe' or lineType == 'oilCPipe' or lineType == 'oilCrudePipe':
			for k1 in range(len(nodes)):
				node = nodes[k1]
				if node.nodeType == 'OilPort':
					primaryNode = node
					primaryNodeIdx = nodeIdxs[k1]
					break
				elif node.nodeType == 'OilTerminal':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
				elif node.nodeType == 'OilRefinery' and primaryNodeType != 'OilTerminal':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
		elif lineType == 'CoalRailroad':
			for k1 in range(len(nodes)):
				node = nodes[k1]
				if node.nodeType == 'CoalDock':
					primaryNode = node
					primaryNodeIdx = nodeIdxs[k1]
					break
				elif node.nodeType == 'CoalSource':
					primaryNode = node
					primaryNodeType = node.nodeType
					primaryNodeIdx = nodeIdxs[k1]
		else:
			print('New line to handle: ' + lineType)
		return primaryNode, primaryNodeIdx

	def setPipeODNames2(self, clusters, resourceIdx):
		"""
		Set the origins and destinations of all lines to the names of the buffers at the endpoints

		:param: self: This takes itself in to set the endpoints
		:return:
		"""
		print('In setPipeODNames')
		count = 0
		verts = self.nodes
		pipes = self.lines
		delLine = []
		clusterPrimary = {}
		clusterRadialCenter = {}
		for i, k1 in enumerate(pipes):
			o = False
			d = False
			k1.controller = []
			if k1.clust_origin not in clusterPrimary:
				foundClustOrigin = np.where(clusters == k1.clust_origin)[0]
				resourcesOrigin = resourceIdx[foundClustOrigin]
				resourcesOrigin = resourcesOrigin[resourcesOrigin >= len(self.lines) * 2]
				if len(resourcesOrigin) > 1:
					primaryNode, primaryNodeIdx = self.findClusterPrimary(k1.type, resourcesOrigin - (len(self.lines) * 2))
					clusterPrimary[k1.clust_origin] = primaryNode
					k1.fBus = clusterPrimary[k1.clust_origin].nodeName
					clusterRadialCenter[primaryNodeIdx] = (k1.type, k1.clust_origin)
				else:
					nodeIdx = resourcesOrigin - (len(self.lines) * 2)
					clusterPrimary[k1.clust_origin] = verts[nodeIdx][0]
					k1.fBus = clusterPrimary[k1.clust_origin].nodeName
			else:
				k1.fBus = clusterPrimary[k1.clust_origin].nodeName
			for controller in clusterPrimary[k1.clust_origin].controller:
				if controller not in k1.controller:
					k1.controller.append(controller)

			if k1.clust_dest not in clusterPrimary:
				foundClustDest = np.where(clusters == k1.clust_dest)[0]
				resourcesDest = resourceIdx[foundClustDest]
				resourcesDest = resourcesDest[resourcesDest >= len(self.lines) * 2]
				if len(resourcesDest) > 1:
					primaryNode, primaryNodeIdx = self.findClusterPrimary(k1.type, resourcesDest - (len(self.lines) * 2))
					clusterPrimary[k1.clust_dest] = primaryNode
					k1.tBus = clusterPrimary[k1.clust_dest].nodeName
					clusterRadialCenter[primaryNodeIdx] = (k1.type, k1.clust_dest)
				else:
					nodeIdx = resourcesDest - (len(self.lines) * 2)
					clusterPrimary[k1.clust_dest] = verts[nodeIdx][0]
					k1.tBus = clusterPrimary[k1.clust_dest].nodeName
			else:
				k1.tBus = clusterPrimary[k1.clust_dest].nodeName
			for controller in clusterPrimary[k1.clust_dest].controller:
				if controller not in k1.controller:
					k1.controller.append(controller)

			if type(k1.fBus) != type('') or type(k1.tBus) != type(''):
				delLine.append(k1)
				print('oh no! line without an origin or dest')

		self.linkClusterBuffers(clusters, resourceIdx, clusterRadialCenter)

		for k3 in np.flip(delLine):
			self.lines = np.delete(self.lines, k3)

	def linkClusterBuffers(self, clusters, resourceIdx, clusterRadialCenter):
		print('linking clustered nodes')

		lines = []
		transmission_count = 0
		NG_count = 0
		OilRefPipe_count = 0
		OilCrudePipe_count = 0
		Railroad_count = 0

		keys = list(clusterRadialCenter.keys())
		for k1 in range(len(keys)):
			primaryNodeIdx = keys[k1]
			primaryNode = self.nodes[primaryNodeIdx]
			lineType = clusterRadialCenter[primaryNodeIdx][0]
			cluster = clusterRadialCenter[primaryNodeIdx][1]
			foundClust = np.where(clusters == cluster)[0]
			clusterResources = resourceIdx[foundClust]
			clusterResources = clusterResources[clusterResources >= len(self.lines) * 2]
			for k2 in clusterResources:
				nodeIdx = k2 - (len(self.lines) * 2)
				if primaryNodeIdx != nodeIdx:
					currentNode = self.nodes[nodeIdx]
					if lineType == 'ElecLine':
						if 'electric power at 132kV' in currentNode.refinement:
							transmission_count += 1
							new_instance = ElectricLine()
							new_instance.lineName = 'Transmission Line Connector ' + str(transmission_count)
							new_instance.refinement = ['electric power at 132kV']
							new_instance.fuelType = ['electric power at 132kV']
							new_instance.attrib_ref = ['electric power at 132kV']
							new_instance.type = 'ElecLine'
					elif lineType == 'NGPipe':
						sharedRef = list(set(primaryNode.refinement) & set(currentNode.refinement))
						if len(sharedRef)>0:
							NG_count += 1
							new_instance = NGPipe()
							new_instance.lineName = 'NG Pipeline Connector ' + str(NG_count)
							new_instance.refinement = sharedRef
							new_instance.fuelType = sharedRef
							new_instance.attrib_ref = sharedRef
							new_instance.type = 'NGPipe'
					elif lineType == 'OilRefPipe':
						sharedRef = list(set(primaryNode.refinement) & set(currentNode.refinement))
						if len(sharedRef)>0:
							OilRefPipe_count += 1
							new_instance = OilRefPipe()
							new_instance.lineName = 'Refined Oil Pipeline Connector ' + str(OilRefPipe_count)
							new_instance.refinement = sharedRef
							new_instance.fuelType = sharedRef
							new_instance.attrib_ref = sharedRef
							new_instance.type = 'OilRefPipe'
					elif lineType == 'OilCrudePipe' or lineType =='oilCrudePipe':
						sharedRef = list(set(primaryNode.refinement) & set(currentNode.refinement))
						if len(sharedRef)>0:
							OilCrudePipe_count += 1
							new_instance = OilCrudePipe()
							new_instance.lineName = 'Crude Oil Pipeline Connector ' + str(OilCrudePipe_count)
							new_instance.refinement = sharedRef
							new_instance.fuelType = sharedRef
							new_instance.attrib_ref = sharedRef
							new_instance.type = 'OilCrudePipe'
					elif lineType == 'CoalRailroad':
						sharedRef = list(set(primaryNode.refinement) & set(currentNode.refinement))
						if len(sharedRef)>0:
							Railroad_count += 1
							new_instance = CoalRailroad()
							new_instance.lineName = 'Coal Railroad Connector ' + str(Railroad_count)
							new_instance.refinement = sharedRef
							new_instance.fuelType = sharedRef
							new_instance.attrib_ref = sharedRef
							new_instance.type = 'CoalRailroad'
					else:
						print('line type not handled. need to handle: ' + lineType)
					new_instance.status = 'true'
					new_instance.clust_origin = cluster
					new_instance.clust_dest = cluster
					new_instance.fBus = primaryNode.nodeName
					new_instance.tBus = currentNode.nodeName
					new_instance.attrib_origin = new_instance.fBus
					new_instance.attrib_dest = new_instance.tBus
					for controller in primaryNode.controller:
						if controller not in new_instance.controller:
							new_instance.controller.append(controller)
					for controller in currentNode.controller:
						if controller not in new_instance.controller:
							new_instance.controller.append(controller)
					lines.append(new_instance)
		self.lines = np.hstack((self.lines, lines))

	def setNodeStates(self):
		"""
		Set the region of each buffer to the state they belong too.
		:param: self: This takes itself in to set the endpoints
		:return:
		"""
		print('In setNodeStates')
		if self.regions.empty == True:
			print('No Controller Regions')
			return
		count = 0
		self.controllers = []
		verts = self.nodes
		all_states = self.regions['geometry']  # get all the polygons
		all_records = self.regions['STUSPS']
		all_ISOs = self.controlAreas['geometry']
		all_ISO_records = self.controlAreas['ISO']
		if hasattr(self, 'NGRegions'):
			all_Regions = self.NGRegions['geometry']
			all_Region_records = self.NGRegions['NAME']
		progress = 0
		for i, k1 in enumerate(verts):
			if progress == 1000:
				print('buffer: ' + str(i) + ' of ' + str(len(verts)))
				progress = 0
			progress += 1
			stateAttrib = False
			k1.controller = []
			if hasattr(k1, 'state'):
				name = k1.state
				if name != None:
					stateAttrib = True
					k1.controller.append(name)
					if name not in self.controllers:
						self.controllers.append(name)
			if not stateAttrib:
				regionFound = False
				coords = [k1.gpsX, k1.gpsY]
				minDist = 999999
				minIdx = 0
				for j in range(len(all_states)):
					boundary = all_states[j]  # get a boundary polygon
					if Point(coords).within(shape(boundary)):  # make a point and see if it's in the polygon
						name = all_records[j]  # get the second field of the corresponding record
						k1.region = name
						k1.controller.append(name)
						if name not in self.controllers:
							self.controllers.append(name)
						regionFound = True
						break
					else:
						dist = Point(coords).distance(shape(boundary))
						if dist < minDist:
							minDist = dist
							minIdx = j
				if not regionFound:
					name = all_records[minIdx]  # get the second field of the corresponding record
					k1.region = name
					k1.controller.append(name)
					if name not in self.controllers:
						self.controllers.append(name)
			if hasattr(k1, 'iso'):
				if k1.iso !=None:
					name = k1.iso
					self.setISO(k1, name)
				else:
					coords = [k1.gpsX, k1.gpsY]
					minDist = 999999
					minIdx = 0
					regionFound = False
					for k2 in range(len(all_ISOs)):
						boundary = all_ISOs[k2]  # get a boundary polygon
						if Point(coords).within(shape(boundary)):  # make a point and see if it's in the polygon
							name = all_ISO_records[k2]  # get the second field of the corresponding record
							self.setISO(k1, name)
							regionFound = True
							break
						else:
							dist = Point(coords).distance(shape(boundary))
							if dist < minDist:
								minDist = dist
								minIdx = k2
					if not regionFound:
						name = all_ISO_records[minIdx]  # get the second field of the corresponding record
						self.setISO(k1, name)
			if k1.nodeType == "NGStorage":
				if k1.region !=None:
					name = k1.region
					self.setRegion(k1, name)
				else:
					coords = [k1.gpsX, k1.gpsY]
					minDist = 999999
					minIdx = 0
					regionFound = False
					for k2 in range(len(all_Regions)):
						boundary = all_Regions[k2]  # get a boundary polygon
						if Point(coords).within(shape(boundary)):  # make a point and see if it's in the polygon
							name = all_Region_records[k2]  # get the second field of the corresponding record
							self.setRegion(k1, name)
							regionFound = True
							break
						else:
							dist = Point(coords).distance(shape(boundary))
							if dist < minDist:
								minDist = dist
								minIdx = k2
					if not regionFound:
						name = all_Region_records[minIdx][2]  # get the second field of the corresponding record
						self.setRegion(k1, name)

	def setRegion(selfself, node, region):
		node.controller.append(region)
		if region not in self.controllers:
			self.controllers.append(region)

	def setController(self, node, state):
		"""
		Set the controllers of the buffers to corresponding controller based on the region.
		:param: self: This takes itself in to set the endpoints
		:return:
		"""
		# if state == "ME":
		# 	node.controller.append("ME")
		# 	if "ME" not in self.controllers:
		# 		self.controllers.append("ME")
		# elif state == "NH":
		# 	node.controller.append("NH")
		# 	if "NH" not in self.controllers:
		# 		self.controllers.append("NH")
		# elif state == "VT":
		# 	node.controller.append("VT")
		# 	if "VT" not in self.controllers:
		# 		self.controllers.append("VT")
		# elif state == "MA":
		# 	node.controller.append("MA")
		# 	if "MA" not in self.controllers:
		# 		self.controllers.append("MA")
		# elif state == "CT":
		# 	node.controller.append("CT")
		# 	if "CT" not in self.controllers:
		# 		self.controllers.append("CT")
		# elif state == "RI":
		# 	node.controller.append("RI")
		# 	if "RI" not in self.controllers:
		# 		self.controllers.append("RI")
		# elif state == "NY":
		# 	node.controller.append("NY")
		# 	if "NY" not in self.controllers:
		# 		self.controllers.append("NY")
		# elif state == "PA":
		# 	node.controller.append("PA")
		# 	if "PA" not in self.controllers:
		# 		self.controllers.append("PA")
		# elif state == "OH":
		# 	node.controller.append("OH")
		# 	if "OH" not in self.controllers:
		# 		self.controllers.append("OH")
		# elif state == "NJ":
		# 	node.controller.append("NJ")
		# 	if "NJ" not in self.controllers:
		# 		self.controllers.append("NJ")
		# elif state == "WV":
		# 	node.controller.append("WV")
		# 	if "WV" not in self.controllers:
		# 		self.controllers.append("WV")
		# elif state == "VA":
		# 	node.controller.append("VA")
		# 	if "VA" not in self.controllers:
		# 		self.controllers.append("VA")
		# elif state == "DE":
		# 	node.controller.append("DE")
		# 	if "DE" not in self.controllers:
		# 		self.controllers.append("DE")
		# else:
		node.controller.append(state)
		if state not in self.controllers:
			self.controllers.append(state)

	def setISO(self, node, ISO):
		"""
		Set the controllers of the buffers to corresponding controller based on the region.
		:param: self: This takes itself in to set the endpoints
		:return:
		"""

		if "NEW ENGLAND" in ISO or "ISONE" in ISO:
			node.controller.append("ISONE")
			if "ISONE" not in self.controllers:
				self.controllers.append("ISONE")
		elif "NEW YORK" in ISO or "NYISO" in ISO:
			node.controller.append("NYISO")
			if "NYISO" not in self.controllers:
				self.controllers.append("NYISO")
		elif "PJM" in ISO:
			node.controller.append("PJM")
			if "PJM" not in self.controllers:
				self.controllers.append("PJM")
		else:
			node.controller.append(ISO)
			if ISO not in self.controllers:
				self.controllers.append(ISO)

	def reviseOil(self):
		"""
		Cluster and clean all buffers and endpoints in the AMES System.
		Add needed Lines and independent buffers to connect the system.
		Remove isolated buffers and lines from the system and join connected lines
		Set origin and destination names for all lines.

		:param self: Takes its own AMES object as an input
		:return: An updated AMES Object with cleaned data
		"""
		print('reviseOil')
		oilPowerPlantIdxs = []
		oilOtherNodes = []
		ptsXOther = []
		ptsYOther = []
		for k1 in range(len(self.nodes)):
			if self.nodes[k1].nodeType == 'GenC' or self.nodes[k1].nodeType == 'GenS':
				if 'processed oil' in self.nodes[k1].fuelType:
					oilPowerPlantIdxs.append(k1)
			elif self.nodes[k1].nodeType == 'OilIndBuffer' or self.nodes[k1].nodeType == 'OilPort' or self.nodes[k1].nodeType == 'OilTerminal':
				oilOtherNodes.append(k1)
				ptsXOther.append(self.nodes[k1].gpsX)
				ptsYOther.append(self.nodes[k1].gpsY)
		processedOilLines = []
		for k2 in range(len(self.lines)):
			if 'processed oil' in self.lines[k2].refinement:
				processedOilLines.append(k2)

		isoNodes = []
		ptsXIso = []
		ptsYIso = []
		for k3 in range(len(oilPowerPlantIdxs)):
			nodeName = self.nodes[oilPowerPlantIdxs[k3]].nodeName
			found = False
			for k4 in range(len(processedOilLines)):
				if nodeName in self.lines[processedOilLines[k4]].fBus or nodeName in self.lines[processedOilLines[k4]].tBus:
					found = True
					break
			if found != True:
				isoNodes.append(oilPowerPlantIdxs[k3])
				ptsXIso.append(self.nodes[oilPowerPlantIdxs[k3]].gpsX)
				ptsYIso.append(self.nodes[oilPowerPlantIdxs[k3]].gpsY)

		print('starting isolated Oil powerplant clustering algorithem...')
		eps = 0.5075*4  # = 35*2 miles (tertiary Clustering Radius for adding lines)
		ptsXIso = np.array(ptsXIso)
		ptsYIso = np.array(ptsYIso)
		ptsXOther = np.array(ptsXOther)
		ptsYOther = np.array(ptsYOther)
		clusters = np.array([None] * len(ptsXIso))
		clust = 0

		print('creating primary cluster')
		stillIsoNode = []
		oilRef_count = 0
		for k1 in range(len(isoNodes)):
			distances = ((ptsXIso[k1] - ptsXOther) ** 2 + (
					ptsYIso[k1] - ptsYOther) ** 2) ** 0.5
			found = np.where(distances <= eps)[0]
			if any(found):
				found_dist = distances[found]
				closest_dist = np.argmin(found_dist)
				closest_node = oilOtherNodes[found[closest_dist]]
				#### create transportation resource to transporting oil to power plants
				oilRef_count += 1
				new_instance = OilRefPipe()
				if self.oilSystem != None:
					new_instance.lineName = 'OilR Pipeline ' + str(len(self.oilSystem.OilRefPipe) + oilRef_count)
				else:
					new_instance.lineName = 'OilR Pipeline ' + str(oilRef_count)
				new_instance.refinement = ['processed oil']
				new_instance.fuelType = ['processed oil']
				new_instance.attrib_ref = ['processed oil']
				new_instance.type = 'oilRPipe'
				new_instance.fBus = self.nodes[closest_node].nodeName
				new_instance.tBus = self.nodes[isoNodes[k1]].nodeName
				new_instance.fBus_gps = (self.nodes[closest_node].gpsX, self.nodes[closest_node].gpsY)
				new_instance.tBus_gps = (self.nodes[isoNodes[k1]].gpsX, self.nodes[isoNodes[k1]].gpsY)
				new_instance.status = 'true'
				new_instance.clust_origin = self.nodes[closest_node].cluster
				new_instance.clust_dest = self.nodes[isoNodes[k1]].cluster
				new_instance.attrib_origin = new_instance.fBus
				new_instance.attrib_dest = new_instance.tBus
				new_instance.controller = []
				for controller in self.nodes[closest_node].controller:
					if controller not in new_instance.controller:
						new_instance.controller.append(controller)
				for controller in self.nodes[isoNodes[k1]].controller:
					if controller not in new_instance.controller:
						new_instance.controller.append(controller)
				self.lines = np.append(self.lines,new_instance)
			else:
				stillIsoNode.append(isoNodes[k1])
		print(len(stillIsoNode))

	def write_xml_hfgt(self, fileout):
		"""
		Creates the HFGT compliant XML file to save the cleaned and organized data.
		This XML can be input into the HFGT Toolbox to produce a HFG.

		:param: fileout: A string designating the name of the output XML
		:return:
		"""
		print('Generating HFGT XML tree ...')

		# This is the root of the ETree where all the information branches from
		root = ET.Element('LFES', OrderedDict([('name', self.name), ('type', 'Energy System'), ('dataState', 'raw')]))

		for k1 in self.refinements:
			operand = ET.SubElement(root, 'Operand', OrderedDict([('name', k1)]))

		for node in self.nodes:
			node.add_xml_child_hfgt(root)
		for line in self.lines:
			line.add_xml_child_hfgt(root)

		self.add_xml_controllers(root)

		self.add_xml_services(root)

		self.add_xml_abstraction_hfgt(root)
		tree = ET.ElementTree(root)

		print('Writing HFGT XML file "{}"...'.format(fileout))
		tree.write(fileout, encoding='utf-8', xml_declaration=True)

	def write_xml_hfgt_dofs(self, fileout):
		"""
		Creates the HFGT compliant XML file to save the cleaned and organized data.
		This XML can be input into the HFGT Toolbox to produce a HFG.

		:param: fileout: A string designating the name of the output XML
		:return:
		"""
		print('Generating HFGT XML tree DOFs...')

		# This is the root of the ETree where all the information branches from
		root = ET.Element('LFES', OrderedDict([('name', self.name), ('type', 'Energy System'), ('dataState', 'raw'), ('numBuffers', str(len(self.nodes)))]))

		print('gathering operands')
		print(self.refinements)
		for k1 in self.refinements:
			operand = ET.SubElement(root, 'Operand', OrderedDict([('name', k1)]))

		resourceCount = [0, 0, 0]
		resourceIdx = {}
		print('gathering nodes')
		for node in self.nodes:
			[resourceCount, resourceIdx] = node.add_xml_child_hfgt_dofs(root, resourceCount, resourceIdx)

		print('gathering lines')
		for line in self.lines:
			resourceCount = line.add_xml_child_hfgt_dofs(root, resourceCount, resourceIdx)

		print("gathering controllers")
		self.add_xml_controllers(root)

		# print('gathering services')
		# self.add_xml_services(root)

		print('gathering abstraction')
		self.add_xml_abstraction_hfgt(root)

		print('Starting regular expression')
		xmlString = tostring(root, encoding='unicode', method='xml')

		print('Starting RE: IndBuffers')
		# set IndBuffer resource idx
		buffers = re.compile("indBuff'.*?'")
		indValue = re.compile("'.*?'")
		foundBuffer = buffers.findall(xmlString)
		uniBuffer = pd.unique(foundBuffer)
		for b1 in range(len(uniBuffer)):
			buff = indValue.search(uniBuffer[b1]).group()[1:-1]
			xmlString = re.sub(uniBuffer[b1], str(int(buff)+resourceCount[0]), xmlString)

		print('Starting RE: Opperands')
		# Set opperands to idx
		operands = re.compile('<Operand name=".*?"')
		value = re.compile('".*?"')
		foundOperand = operands.findall(xmlString)
		uniOperand = pd.unique(foundOperand)
		for k1 in range(len(uniOperand)):
			oper = value.search(uniOperand[k1]).group()[1:-1]
			xmlString = re.sub('Operand name="' + oper, 'Operand name="' + str(k1), xmlString)
			xmlString = re.sub('operand="' + oper, 'operand="' + str(k1), xmlString)
			xmlString = re.sub('output="' + oper, 'output="' + str(k1), xmlString)
			xmlString = re.sub(', ' + oper, ', ' + str(k1), xmlString)

		print('Starting RE: Refinements')
		# set Refinements to idx
		Abstraction = re.compile(r"<Abstractions>.*?/Abstractions>", re.DOTALL)
		refinement = re.compile('ref=".*?"')
		foundAbs = Abstraction.findall(xmlString)[0]
		foundRef = refinement.findall(foundAbs)
		uniRef = pd.unique(foundRef)
		for k1 in range(len(uniRef)):
			xmlString = re.sub(uniRef[k1], 'ref="' + str(k1) + '"', xmlString)
			xmlString = re.sub('ref1=' + value.search(uniRef[k1]).group(), 'ref1="' + str(k1) + '"', xmlString)
			xmlString = re.sub('ref2=' + value.search(uniRef[k1]).group(), 'ref2="' + str(k1) + '"', xmlString)
			xmlString = re.sub('methodLinkRef=' + value.search(uniRef[k1]).group(), 'methodLinkRef="' + str(k1) + '"',xmlString)

		print('Starting RE: Controllers')
		# set controllers to idx
		controllers = re.compile('<Controller name=".*?"')
		foundCont = controllers.findall(xmlString)
		for k1 in range(len(foundCont)):
			control = value.search(foundCont[k1]).group()[1:-1]
			print(control + ' : ' + str(k1))
			xmlString = re.sub('"' + control + '"', '"' + str(k1) + '"', xmlString)
			xmlString = re.sub('"' + control + ',', '"' + str(k1) + ',', xmlString)
			xmlString = re.sub(', ' + control + ',', ', ' + str(k1) + ',', xmlString)
			xmlString = re.sub(', ' + control + '"', ', ' + str(k1) + '"', xmlString)
			xmlString = re.sub(foundCont[k1][0:18] + str(k1) + '"', foundCont[k1][0:18] + str(k1) + '" nameStr="' + control + '"', xmlString)

		print('Starting RE: MethodxForm')
		methodxForm = re.compile('\<MethodxForm .*?\>')
		foundMF = methodxForm.findall(xmlString)
		concatenated_strings = "".join(foundMF)
		name = re.compile('name=".*?"')
		foundMXFName = name.findall(concatenated_strings)
		uniMXF = pd.unique(foundMXFName)
		for k1 in range(len(uniMXF)):
			xmlString = re.sub(uniMXF[k1], uniMXF[k1] + ' idxProc="' + str(k1) + '" ', xmlString)
			proc = value.search(uniMXF[k1]).group()
			xmlString = re.sub('name1=' + proc, 'name1="' + str(k1) + '"', xmlString)
			xmlString = re.sub('name2=' + proc, 'name2="' + str(k1) + '"', xmlString)
			xmlString = re.sub('methodLinkName=' + proc, 'methodLinkIdx="' + str(k1) + '" methodLinkName=' + proc, xmlString)
		if not k1:
			k1 = -1
		xmlString = re.sub('methodLinkName="transport"', 'methodLinkIdx="' + str(k1 + 1) + '" methodLinkName="transport"',xmlString)
		xmlString = re.sub('methodLinkName="store"', 'methodLinkIdx="' + str(k1 + 1) + '" methodLinkName="store"', xmlString)

		print('Compiling tree before writing to XML file')
		root = ET.fromstring(xmlString)
		tree = ET.ElementTree(root)

		print('Writing HFGT XML file "{}"...'.format(fileout))
		tree.write(fileout, encoding='utf-8', xml_declaration=True)

	def add_xml_controllers(self, root):
		print(self.controllers)
		for k1 in self.controllers:
			controller = ET.SubElement(root, 'Controller', OrderedDict([('name', k1), ('status', 'true')]))
			if k1 == "ISONE":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ME")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NH")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "VT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "RI")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NYISO")]))
			elif k1 == "NYISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NY")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ISONE")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "PJM")]))
			elif k1 == "CAISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NWISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SWISO")]))
			elif k1 == "NWISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "WA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "OR")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ID")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "WY")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "UT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CAISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SWISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SPP")]))
			elif k1 == "SWISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NV")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "AZ")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NM")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CAISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NWISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SPP")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ERCOT")]))
			elif k1 == "ERCOT":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TX")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SWISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SPP")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MISO")]))
			elif k1 == "SPP":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ND")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SD")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NE")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "KS")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "OK")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TX")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "AR")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ERCOT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SWISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NWISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MISO")]))
			elif k1 == "MISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ND")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MN")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "IA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "AR")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "LA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TX")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "WI")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "IL")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "IN")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MI")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "KY")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MS")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "ERCOT")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SPP")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "PJM")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TNISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SOCO")]))
			elif k1 == "TNISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "KY")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TN")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "LA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MS")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "AL")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NC")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "VA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "PJM")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SOCO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CARISO")]))
			elif k1 == "SOCO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MS")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "AL")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "GA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "FL")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TNISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CARISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "FPISO")]))
			elif k1 == "FPISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "FL")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SOCO")]))
			elif k1 == "CARISO":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SC")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NC")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "SOCO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TNISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "PJM")]))
			elif k1 == "PJM":
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NC")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "VA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TN")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "KY")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "WV")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "OH")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "IN")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MI")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "IL")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MD")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "DE")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "PA")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NJ")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "CARISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "TNISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "MISO")]))
				peerRecipient = ET.SubElement(controller, 'PeerRecipient', OrderedDict([('name', "NYISO")]))
			else:
				print(k1)

	def add_xml_services(self, root):
		service = ET.SubElement(root, 'Service', OrderedDict([('name', 'deliverElectricity'), ('status', 'true')]))
		if self.elecGrid != None:
			abstraction = ET.SubElement(service, 'ServicePlace', OrderedDict([('name', 'electric power at 132kV')]))
			abstraction = ET.SubElement(service, 'ServiceTransition', OrderedDict(
				[('name', 'generate electric power'), ('preset', ''), ('postset', 'electric power at 132kV'),
				 ('methodLinkName', 'generate electric power'), ('methodLinkRef', '')]))
			abstraction = ET.SubElement(service, 'ServiceTransition', OrderedDict(
				[('name', 'continuing electric power'), ('preset', 'electric power at 132kV'),
				 ('postset', 'electric power at 132kV'), ('methodLinkName', 'transport'),
				 ('methodLinkRef', 'electric power at 132kV')]))
			abstraction = ET.SubElement(service, 'ServiceTransition', OrderedDict(
				[('name', 'consume electric power'), ('preset', 'electric power at 132kV'), ('postset', ''),
				 ('methodLinkName', 'consume electric power'), ('methodLinkRef', '')]))

	def add_xml_abstraction_hfgt(self, root):

		abstractions = ET.SubElement(root, 'Abstractions')

		# output all MethodxForms and MethodxPorts
		if 'electric power at 132kV' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'electric power at 132kV'), ('operand', 'electric power at 132kV'),
				 ('output', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'electric power at 132kV'), ('operand', 'electric power at 132kV'),
				 ('output', 'electric power at 132kV')]))
		if 'processed gas' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'processed gas'), ('operand', 'processed gas'),
				 ('output', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'processed gas'), ('operand', 'processed gas'),
				 ('output', 'processed gas')]))
		if 'syngas' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'syngas'), ('operand', 'syngas'), ('output', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'syngas'), ('operand', 'syngas'), ('output', 'syngas')]))
		if 'raw gas' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'raw gas'), ('operand', 'raw gas'), ('output', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'raw gas'), ('operand', 'raw gas'), ('output', 'raw gas')]))
		if 'crude oil' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'crude oil'), ('operand', 'crude oil'), ('output', 'crude oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'crude oil'), ('operand', 'crude oil'), ('output', 'crude oil')]))
		if 'processed oil' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'processed oil'), ('operand', 'processed oil'),
				 ('output', 'processed oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'processed oil'), ('operand', 'processed oil'),
				 ('output', 'processed oil')]))
		if 'liquid biomass feedstock' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'liquid biomass feedstock'), ('operand', 'liquid biomass feedstock'),
				 ('output', 'liquid biomass feedstock')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'liquid biomass feedstock'), ('operand', 'liquid biomass feedstock'),
				 ('output', 'liquid biomass feedstock')]))
		if 'solid biomass feedstock' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'solid biomass feedstock'), ('operand', 'solid biomass feedstock'),
				 ('output', 'solid biomass feedstock')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'solid biomass feedstock'), ('operand', 'solid biomass feedstock'),
				 ('output', 'solid biomass feedstock')]))
		if 'coal' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'coal'), ('operand', 'coal'), ('output', 'coal')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'coal'), ('operand', 'coal'), ('output', 'coal')]))
		if 'water energy' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'water energy'), ('operand', 'water energy'), ('output', 'water energy')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'water energy'), ('operand', 'water energy'), ('output', 'water energy')]))
		if 'other' in self.refinements:
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'transport'), ('ref', 'other'), ('operand', 'other'), ('output', 'other')]))
			abstraction = ET.SubElement(abstractions, 'MethodxPort', OrderedDict(
				[('name', 'store'), ('ref', 'other'), ('operand', 'other'), ('output', 'other')]))


		# add all MethodPairs
		if self.elecGrid != None:
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'generate electric power'), ('ref1', ''), ('name2', 'store'),
			# 	 ('ref2', 'electric power at 132kV')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'generate electric power'), ('ref1', ''), ('name2', 'transport'),
			# 	 ('ref2', 'electric power at 132kV')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'generate electric power'), ('ref1', ''), ('name2', 'consume electric power'),
			# 	 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from processed gas'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from processed gas'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from processed gas'), ('ref1', ''),
				 ('name2', 'consume electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from processed oil'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from processed oil'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from processed oil'), ('ref1', ''),
				 ('name2', 'consume electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from syngas'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from syngas'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from syngas'), ('ref1', ''), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from coal'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from coal'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from coal'), ('ref1', ''), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from uranium'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from uranium'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from uranium'), ('ref1', ''), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from solid biomass feedstock'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from solid biomass feedstock'), ('ref1', ''),
				 ('name2', 'transport'), ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from solid biomass feedstock'), ('ref1', ''),
				 ('name2', 'consume electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from liquid biomass feedstock'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from liquid biomass feedstock'), ('ref1', ''),
				 ('name2', 'transport'), ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from liquid biomass feedstock'), ('ref1', ''),
				 ('name2', 'consume electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from other'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from other'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from other'), ('ref1', ''), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from water energy'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from water energy'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from water energy'), ('ref1', ''),
				 ('name2', 'consume electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from solar'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from solar'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from solar'), ('ref1', ''), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from wind energy'), ('ref1', ''), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from wind energy'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'generate electric power from wind energy'), ('ref1', ''),
				 ('name2', 'consume electric power'), ('ref2', '')]))

			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'electric power at 132kV'), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'electric power at 132kV'), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'electric power at 132kV'), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'electric power at 132kV'), ('name2', 'consume electric power'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'electric power at 132kV'), ('name2', 'transport'),
				 ('ref2', 'electric power at 132kV')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'electric power at 132kV'), ('name2', 'store'),
				 ('ref2', 'electric power at 132kV')]))

		if self.NGSystem != None:
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import raw gas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import raw gas'), ('ref1', ''), ('name2', 'store'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'raw gas'), ('name2', 'transport'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'raw gas'), ('name2', 'store'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'raw gas'), ('name2', 'store'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'raw gas'), ('name2', 'transport'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'raw gas'), ('name2', 'compress raw gas'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'compress raw gas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'raw gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'raw gas'), ('name2', 'process raw gas'), ('ref2', '')]))

			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'process raw gas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import processed gas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import processed gas'), ('ref1', ''), ('name2', 'store'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed gas'), ('name2', 'transport'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed gas'), ('name2', 'store'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'processed gas'), ('name2', 'store'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'processed gas'), ('name2', 'transport'), ('ref2', 'processed gas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed gas'), ('name2', 'compress processed gas'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'compress processed gas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'processed gas')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'transport'), ('ref1', 'processed gas'), ('name2', 'generate electric power'),
			# 	 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed gas'),
				 ('name2', 'generate electric power from processed gas'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed gas'), ('name2', 'export processed gas'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'processed gas'), ('name2', 'export processed gas'), ('ref2', '')]))

			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import syngas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import syngas'), ('ref1', ''), ('name2', 'store'), ('ref2', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'syngas'), ('name2', 'transport'), ('ref2', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'syngas'), ('name2', 'store'), ('ref2', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'syngas'), ('name2', 'store'), ('ref2', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'syngas'), ('name2', 'transport'), ('ref2', 'syngas')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'syngas'), ('name2', 'compress syngas'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'compress syngas'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'syngas')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'transport'), ('ref1', 'syngas'), ('name2', 'generate electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'syngas'), ('name2', 'generate electric power from syngas'),
				 ('ref2', '')]))

		if self.oilSystem != None:
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import crude oil'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'crude oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'crude oil'), ('name2', 'transport'), ('ref2', 'crude oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'crude oil'), ('name2', 'store'), ('ref2', 'crude oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'crude oil'), ('name2', 'export crude oil'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'crude oil'), ('name2', 'process crude oil'), ('ref2', '')]))

			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'process crude oil'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'processed oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import processed oil'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'processed oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import processed oil'), ('ref1', ''), ('name2', 'store'), ('ref2', 'processed oil')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'import processed oil'), ('ref1', ''), ('name2', 'export processed oil'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed oil'), ('name2', 'transport'), ('ref2', 'processed oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed oil'), ('name2', 'store'), ('ref2', 'processed oil')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'transport'), ('ref1', 'processed oil'), ('name2', 'generate electric power'),
			# 	 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed oil'),
				 ('name2', 'generate electric power from processed oil'), ('ref2', '')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'store'), ('ref1', 'processed oil'), ('name2', 'generate electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'processed oil'), ('name2', 'generate electric power from processed oil'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'processed oil'), ('name2', 'export processed oil'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'processed oil'), ('name2', 'export processed oil'), ('ref2', '')]))

			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import liquid biomass feedstock'), ('ref1', ''), ('name2', 'transport'),
				 ('ref2', 'liquid biomass feedstock')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'liquid biomass feedstock'), ('name2', 'transport'),
				 ('ref2', 'processed oil')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'liquid biomass feedstock'), ('name2', 'store'),
				 ('ref2', 'liquid biomass feedstock')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'liquid biomass feedstock'),
				 ('name2', 'export liquid biomass feedstock'), ('ref2', '')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'transport'), ('ref1', 'liquid biomass feedstock'), ('name2', 'generate electric power'),
			# 	 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'liquid biomass feedstock'),
				 ('name2', 'generate electric power from liquid biomass feedstock'), ('ref2', '')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'store'), ('ref1', 'liquid biomass feedstock'), ('name2', 'generate electric power'),
			# 	 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'liquid biomass feedstock'),
				 ('name2', 'generate electric power from liquid biomass feedstock'), ('ref2', '')]))

		if self.coalSystem != None:
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import coal'), ('ref1', ''), ('name2', 'transport'), ('ref2', 'coal')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'import coal'), ('ref1', ''), ('name2', 'store'), ('ref2', 'coal')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'coal'), ('name2', 'transport'), ('ref2', 'coal')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'coal'), ('name2', 'store'), ('ref2', 'coal')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'coal'), ('name2', 'generate electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'coal'), ('name2', 'generate electric power from coal'),
				 ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'coal'), ('name2', 'transport'), ('ref2', 'coal')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'coal'), ('name2', 'store'), ('ref2', 'coal')]))
			# abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
			# 	[('name1', 'store'), ('ref1', 'coal'), ('name2', 'generate electric power'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'coal'), ('name2', 'generate electric power from coal'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'transport'), ('ref1', 'coal'), ('name2', 'export coal'), ('ref2', '')]))
			abstraction = ET.SubElement(abstractions, 'MethodPair', OrderedDict(
				[('name1', 'store'), ('ref1', 'coal'), ('name2', 'export coal'), ('ref2', '')]))
