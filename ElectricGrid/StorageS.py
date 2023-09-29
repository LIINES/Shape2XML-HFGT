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

class StorageS(ElectricNode):
    """
    This Class represents all power system's stochastic storage devices.

    Attributes:
        storageSNum:
        storageSType:
        maxP:
        minP:
        maxQ:
        rNode:
        xNode:
        costL:
        nodeType:

    """
    def __init__(self):
        """
        This function instantiates the storage device with attributes set to none type.
        """
        ElectricNode.__init__(self)
        self.storageSNum = None
        self.storageSType = None
        self.storageSName = None
        self.maxP = None
        self.minP = None
        self.maxQ = None
        self.minQ = None
        self.rNode = None
        self.xNode = None
        self.costL = None
        self.controller = []
        self.nodeType = self.__class__.__name__

    def add_xml_child_hfgt(self,parent):
        """
        This creates an XML branch for the StorageS object with functionality.
        """

        indBuffer = ET.SubElement(parent, 'IndBuffer', OrderedDict([('name', self.storageSName), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('controller',', '.join(self.controller))]))
        method_port = ET.SubElement(indBuffer, 'MethodxPort', OrderedDict([('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', self.storageSName), ('dest', self.storageSName), ('ref', 'electric power at 132kV'),('status','true')]))

    def add_xml_child_hfgt_dofs(self,parent,resourceCount, resourceIdx):
        """
        This creates an XML branch for the StorageS object with functionality.
        """
        resource = resourceCount[1]
        method_port = ET.SubElement(parent, 'MethodxPort', OrderedDict([('resource', "indBuff'"+str(resource)+"'"), ('gpsX', str(self.gpsX)), ('gpsY', str(self.gpsY)), ('name', 'store'), ('operand', 'electric power at 132kV'), ('output', 'electric power at 132kV'), ('origin', "indBuff'"+str(resource)+"'"), ('dest', "indBuff'"+str(resource)+"'"), ('ref', 'electric power at 132kV'),('status','true'), ('controller',', '.join(self.controller))]))

        resourceCount[1] += 1
        resourceIdx[self.storageSName] = "indBuff'"+str(resource)+"'"
        return resourceCount, resourceIdx