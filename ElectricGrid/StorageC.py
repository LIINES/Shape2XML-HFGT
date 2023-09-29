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

class StorageC(ElectricNode):
    """
    This class represents all power system's controllable storage.

    Attributes:
        storageCName:      specifies the number of the storage unit
        storageCType:     specifies the type of storage device
        maxPup:          maximum generation power
        minPup:          minimum generation power
        maxE:            maximum reservoir level
        minE:            minimum reservoir level
        maxPdn:          maximum pumping power
        minPdn:          minimum pumping power
        maxQ:            maximum reactive power
        minQ:            minimum reactive power
        efficiency:      storage device efficiency
        eLevel:          storage energy level
        eCost:           cost of stored energy
        pCost:           cost of power stored
        rNode:           resistive node
        xNode:           reactive node
        status1:         status for current SCED
        status2:         status for next SCED
    """

    def __init__(self):
        """
        This function creates an instance of the storage class with attributes set to none type.

        Example use:
        my_storage = StorageC()
        >> my_storage
        >>
        """
        ElectricNode.__init__(self)
        self.nodeType = self.__class__.__name__
        self.storageCType = None
        self.storageCName = None
        self.maxPup = None
        self.minPup = None
        self.maxE = None
        self.minE = None
        self.maxPdn = None
        self.minPdn = None
        self.maxQ = None
        self.minQ = None
        self.rNode = None
        self.xNode = None
        self.status1 = None
        self.status2 = None
        self.efficiency = None
        self.eLevel = None
        self.eCost = None
        self.pCost = None
        self.controller = []

    def add_xml_child_hfgt(self, parent):
        """
        This creates an XML branch for the StorageC object with functionality.
        """
        indBuffer = ET.SubElement(parent, 'IndBuffer', OrderedDict([('name', self.storageCName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
        method_port = ET.SubElement(indBuffer, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', self.storageCName), ('dest', self.storageCName), ('ref', 'electric power at 132kV'),('status','true')]))
    def add_xml_child_hfgt_dofs(self, parent, resourceCount, resourceIdx):
        """
        This creates an XML branch for the StorageC object with functionality.
        """
        resource = resourceCount[1]
        method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict([('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', "indBuff'"+str(resource)+"'"), ('dest', "indBuff'"+str(resource)+"'"), ('ref', 'electric power at 132kV'),('status','true'), ('controller',', '.join(self.controller))]))
        resourceCount[1] += 1
        resourceIdx[self.storageCName] = "indBuff'"+str(resource)+"'"
        return resourceCount, resourceIdx