
"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023

Interprets SHP files exported from QGIS and reads into an AMES object.
From the AMES object, export data as a HFGT-compatible XML file.
"""

import sys
from AMES import AMES
import time
import pickle

def AMES_SHP2XML(energy, region, file_out, DOFS=False):
    """
    Instantiate an AMES object and populate with the desired energy sectors from the designated region.

    AMES_obj = AMES_SHP2XML(['elec', 'NG', 'oil', 'coal'], 'US', 'Output_AMES_US_elec_NG_oil_coal.xml')

    :param energy: List of string designating energy sectors
    :param region: String designating geographical region
    :param file_out: String designating name of the output XML file to be produced
    :param DOFs: boolean input for XML to be in DOF Idx format (True) or object oriented string (False)
    :return grid: The populated AMES python object
    """

    print('making AMES System')

    start_t = time.time()

    grid = AMES()

    exported_files = fetchFileNames('region', region)
    grid.initialize_regions(exported_files)

    if 'elec' in energy:
        exported_files = fetchFileNames('elec', region)
        grid.initialize_electric_grid(exported_files)

    if 'NG' in energy:
        exported_files = fetchFileNames('NG', region)
        grid.initialize_NG_system(exported_files)

    if 'oil' in energy:
        exported_files = fetchFileNames('oil', region)
        grid.initialize_Oil_system(exported_files)

    if 'coal' in energy:
        exported_files = fetchFileNames('coal', region)
        grid.initialize_Coal_system(exported_files)

    grid.reviseAMES()

    grid.reviseOil()

    print('Saving XML')
    if DOFS:
        grid.write_xml_hfgt_dofs(file_out)
    else:
        grid.write_xml_hfgt(file_out)
    end_t = time.time()
    print('Total time to make AMES and XML: %f' % (end_t - start_t))

    return grid

def fetchFileNames(energy, region):
    """
    Fetch the file names of the GIS shape files to populate the AMES based on energy and region.

    :param energy: String designating energy sector
    :param region: String designating geographical region
    :return exported_files: list of strings giving the shape file names
    """
    path = "../../0-Data/0-RawData/ThesisShapes/"

    if energy == 'elec' or energy == 'Elec':
        print('For elec:')
        if region == 'USA':
            print('Fetching US')
            exported_files = [
                path+'USA/Elec/Elec_PowerPlants_US.shp',
                path+'USA/Elec/Elec_Substations_US.shp',
                path+'USA/Elec/Elec_Transmission_Lines_US.shp',
            ]
        elif region == 'EastCoast':
            print('Fetching EastCoast')
            exported_files = [
                path+'EastCoast/Elec/Elec_PowerPlants_EC.shp',
                path+'EastCoast/Elec/Elec_Substations_EC.shp',
                path+'EastCoast/Elec/Elec_Transmission_Lines_EC.shp',
            ]
        elif region == 'EasternInterconnect':
            print('Fetching EasternInterconnect')
            exported_files = [
                path+'EasternInterconnect/Elec/Elec_PowerPlants_EasternInterconnect.shp',
                path+'EasternInterconnect/Elec/Elec_Substations_EasternInterconnect.shp',
                path+'EasternInterconnect/Elec/Elec_Transmission_Lines_EasternInterconnect.shp',
            ]
        elif region == 'WestCoast':
            print('Fetching WestCoast')
            exported_files = [
                path+'WestCoast/Elec/Elec_PowerPlants_WC.shp',
                path+'WestCoast/Elec/Elec_Substations_WC.shp',
                path+'WestCoast/Elec/Elec_Transmission_Lines_WC.shp',
            ]
        elif region == 'Texas':
            print('Fetching WestCoast')
            exported_files = [
                path+'Texas/Elec/Elec_PowerPlants_Texas.shp',
                path+'Texas/Elec/Elec_Substations_Texas.shp',
                path+'Texas/Elec/Elec_Transmission_Lines_Texas.shp',
            ]
        elif region == 'Central':
            print('Fetching Central')
            exported_files = [
                path+'Central/Elec/Elec_PowerPlants_Cent.shp',
                path+'Central/Elec/Elec_Substations_Cent.shp',
                path+'Central/Elec/Elec_Transmission_Lines_Cent.shp',
            ]
        elif region == 'NE_NY':
            print('Fetching NE_NY')
            exported_files = [
                path+'NE_NY/Elec/Elec_PowerPlants_NE_NY.shp',
                path+'NE_NY/Elec/Elec_Substations_NE_NY.shp',
                path+'NE_NY/Elec/Elec_Transmission_Lines_NE_NY.shp',
            ]
        else:
            print('{} is not a handled region for Elec. please input: \'US\', \'TX\', \'CA\', \'NY\'')
            print(region)
            return
    elif energy == 'NG' or energy =='ng':
        print('For NG:')
        if region == 'USA':
            print('Fetching US')
            exported_files = [
                path+'USA/NatGas/NatGas_Compressors_US.shp',
                path+'USA/NatGas/NatGas_LNG_US.shp',
                path+'USA/NatGas/NatGas_Pipelines_US.shp',
                path+'USA/NatGas/NatGas_PowerPlants_US.shp',
                path+'USA/NatGas/NatGas_Receipt_Delivery_US.shp',
                path+'USA/NatGas/NatGas_Hubs_US.shp',
                path+'USA/NatGas/NatGas_Processing_US.shp',
                path+'USA/NatGas/NatGas_Storage_US.shp',
                path+'USA/NGL/NGL_Dehydrogenation_US.shp',
                path+'USA/NGL/NGL_Fractionation_US.shp',
                path+'USA/NGL/NGL_LNG_Terminals_US.shp',
                path+'USA/NGL/NGL_LPG_Export_US.shp',
                path+'USA/NGL/NGL_Processing_US.shp',
                path+'USA/NGL/NGL_Refined_Product_Pipelines_US.shp',
                path+'USA/NGL/NGL_Steam_Crackers_US.shp'
            ]
        elif region == 'EastCoast':
            print('Fetching EastCoast')
            exported_files = [
                path + 'EastCoast/NatGas/NatGas_Compressors_EC.shp',
                path + 'EastCoast/NatGas/NatGas_LNG_EC.shp',
                path + 'EastCoast/NatGas/NatGas_Pipelines_EC.shp',
                path + 'EastCoast/NatGas/NatGas_PowerPlants_EC.shp',
                path + 'EastCoast/NatGas/NatGas_Receipt_Delivery_EC.shp',
                path + 'EastCoast/NatGas/NatGas_Hubs_EC.shp',
                path + 'EastCoast/NatGas/NatGas_Processing_EC.shp',
                path + 'EastCoast/NatGas/NatGas_Storage_EC.shp',
                path + 'EastCoast/NGL/NGL_Dehydrogenation_EC.shp',
                path + 'EastCoast/NGL/NGL_Fractionation_EC.shp',
                path + 'EastCoast/NGL/NGL_LNG_Terminals_EC.shp',
                path + 'EastCoast/NGL/NGL_LPG_Export_EC.shp',
                path + 'EastCoast/NGL/NGL_Processing_EC.shp',
                path + 'EastCoast/NGL/NGL_Refined_Product_Pipelines_EC.shp',
                path + 'EastCoast/NGL/NGL_Steam_Crackers_EC.shp'
            ]
        elif region == 'EasternInterconnect':
            print('Fetching EasternInterconnect')
            exported_files = [
                path + 'EasternInterconnect/NatGas/NatGas_Compressors_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_LNG_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_Pipelines_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_PowerPlants_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_Receipt_Delivery_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_Hubs_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_Processing_EasternInterconnect.shp',
                path + 'EasternInterconnect/NatGas/NatGas_Storage_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_Dehydrogenation_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_Fractionation_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_LNG_Terminals_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_LPG_Export_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_Processing_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_Refined_Product_Pipelines_EasternInterconnect.shp',
                path + 'EasternInterconnect/NGL/NGL_Steam_Crackers_EasternInterconnect.shp'
            ]
        elif region == 'WestCoast':
            print('Fetching WestCoast')
            exported_files = [
                path + 'WestCoast/NatGas/NatGas_Compressors_WC.shp',
                path + 'WestCoast/NatGas/NatGas_LNG_WC.shp',
                path + 'WestCoast/NatGas/NatGas_Pipelines_WC.shp',
                path + 'WestCoast/NatGas/NatGas_PowerPlants_WC.shp',
                path + 'WestCoast/NatGas/NatGas_Receipt_Delivery_WC.shp',
                path + 'WestCoast/NatGas/NatGas_Hubs_WC.shp',
                path + 'WestCoast/NatGas/NatGas_Processing_WC.shp',
                path + 'WestCoast/NatGas/NatGas_Storage_WC.shp',
                path + 'WestCoast/NGL/NGL_Dehydrogenation_WC.shp',
                path + 'WestCoast/NGL/NGL_Fractionation_WC.shp',
                path + 'WestCoast/NGL/NGL_LNG_Terminals_WC.shp',
                path + 'WestCoast/NGL/NGL_LPG_Export_WC.shp',
                path + 'WestCoast/NGL/NGL_Processing_WC.shp',
                path + 'WestCoast/NGL/NGL_Refined_Product_Pipelines_WC.shp',
                path + 'WestCoast/NGL/NGL_Steam_Crackers_WC.shp'
            ]
        elif region == 'Texas':
            print('Fetching Texas')
            exported_files = [
                path + 'Texas/NatGas/NatGas_Compressors_Texas.shp',
                path + 'Texas/NatGas/NatGas_LNG_Texas.shp',
                path + 'Texas/NatGas/NatGas_Pipelines_Texas.shp',
                path + 'Texas/NatGas/NatGas_PowerPlants_Texas.shp',
                path + 'Texas/NatGas/NatGas_Receipt_Delivery_Texas.shp',
                path + 'Texas/NatGas/NatGas_Hubs_Texas.shp',
                path + 'Texas/NatGas/NatGas_Processing_Texas.shp',
                path + 'Texas/NatGas/NatGas_Storage_Texas.shp',
                path + 'Texas/NGL/NGL_Dehydrogenation_Texas.shp',
                path + 'Texas/NGL/NGL_Fractionation_Texas.shp',
                path + 'Texas/NGL/NGL_LNG_Terminals_Texas.shp',
                path + 'Texas/NGL/NGL_LPG_Export_Texas.shp',
                path + 'Texas/NGL/NGL_Processing_Texas.shp',
                path + 'Texas/NGL/NGL_Refined_Product_Pipelines_Texas.shp',
                path + 'Texas/NGL/NGL_Steam_Crackers_Texas.shp'
            ]
        elif region == 'Central':
            print('Fetching Central')
            exported_files = [
                path + 'Central/NatGas/NatGas_Compressors_Cent.shp',
                path + 'Central/NatGas/NatGas_LNG_Cent.shp',
                path + 'Central/NatGas/NatGas_Pipelines_Cent.shp',
                path + 'Central/NatGas/NatGas_PowerPlants_Cent.shp',
                path + 'Central/NatGas/NatGas_Receipt_Delivery_Cent.shp',
                path + 'Central/NatGas/NatGas_Hubs_Cent.shp',
                path + 'Central/NatGas/NatGas_Processing_Cent.shp',
                path + 'Central/NatGas/NatGas_Storage_Cent.shp',
                path + 'Central/NGL/NGL_Dehydrogenation_Cent.shp',
                path + 'Central/NGL/NGL_Fractionation_Cent.shp',
                path + 'Central/NGL/NGL_LNG_Terminals_Cent.shp',
                path + 'Central/NGL/NGL_LPG_Export_Cent.shp',
                path + 'Central/NGL/NGL_Processing_Cent.shp',
                path + 'Central/NGL/NGL_Refined_Product_Pipelines_Cent.shp',
                path + 'Central/NGL/NGL_Steam_Crackers_Cent.shp'
            ]
        elif region == 'NE_NY':
            print('Fetching NE_NY')
            exported_files = [
                path + 'NE_NY/NatGas/NatGas_Compressors_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_LNG_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_Pipelines_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_PowerPlants_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_Receipt_Delivery_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_Hubs_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_Processing_NE_NY.shp',
                path + 'NE_NY/NatGas/NatGas_Storage_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_Dehydrogenation_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_Fractionation_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_LNG_Terminals_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_LPG_Export_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_Processing_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_Refined_Product_Pipelines_NE_NY.shp',
                path + 'NE_NY/NGL/NGL_Steam_Crackers_NE_NY.shp'
            ]
        else:
            print('{} is not a handled region. please input: \'US\', \'TX\', \'CA\', \'NY\'')
            return
    elif energy == 'oil' or energy =='Oil':
        print('For oil:')
        if region == 'USA':
            print('Fetching USA')
            exported_files = [
                path+'USA/Oil/Oil_PowerPlants_US.shp',
                path+'USA/Oil/Oil_Terminals_US.shp',
                path+'USA/Oil/Oil_Pipelines_US.shp',
                path+'USA/Oil/Oil_Refined_Product_Pipelines_US.shp',
                path+'USA/Oil/Oil_Refineries_US.shp',
                path+'USA/Oil/Oil_Ports_US.shp'
            ]
        elif region == 'EastCoast':
            print('Fetching EastCoast')
            exported_files = [
                path + 'EastCoast/Oil/Oil_PowerPlants_EC.shp',
                path + 'EastCoast/Oil/Oil_Terminals_EC.shp',
                path + 'EastCoast/Oil/Oil_Pipelines_EC.shp',
                path + 'EastCoast/Oil/Oil_Refined_Product_Pipelines_EC.shp',
                path + 'EastCoast/Oil/Oil_Refineries_EC.shp',
                path + 'EastCoast/Oil/Oil_Ports_EC.shp'
            ]
        elif region == 'EasternInterconnect':
            print('Fetching EasternInterconnect')
            exported_files = [
                path + 'EasternInterconnect/Oil/Oil_PowerPlants_EasternInterconnect.shp',
                path + 'EasternInterconnect/Oil/Oil_Terminals_EasternInterconnect.shp',
                path + 'EasternInterconnect/Oil/Oil_Pipelines_EasternInterconnect.shp',
                path + 'EasternInterconnect/Oil/Oil_Refined_Product_Pipelines_EasternInterconnect.shp',
                path + 'EasternInterconnect/Oil/Oil_Refineries_EasternInterconnect.shp',
                path + 'EasternInterconnect/Oil/Oil_Ports_EasternInterconnect.shp'
            ]
        elif region == 'WestCoast':
            print('Fetching WestCoast')
            exported_files = [
                path + 'WestCoast/Oil/Oil_PowerPlants_WC.shp',
                path + 'WestCoast/Oil/Oil_Terminals_WC.shp',
                path + 'WestCoast/Oil/Oil_Pipelines_WC.shp',
                path + 'WestCoast/Oil/Oil_Refined_Product_Pipelines_WC.shp',
                path + 'WestCoast/Oil/Oil_Refineries_WC.shp',
                path + 'WestCoast/Oil/Oil_Ports_WC.shp'
            ]
        elif region == 'Texas':
            print('Fetching Texas')
            exported_files = [
                path + 'Texas/Oil/Oil_PowerPlants_Texas.shp',
                path + 'Texas/Oil/Oil_Terminals_Texas.shp',
                path + 'Texas/Oil/Oil_Pipelines_Texas.shp',
                path + 'Texas/Oil/Oil_Refined_Product_Pipelines_Texas.shp',
                path + 'Texas/Oil/Oil_Refineries_Texas.shp',
                path + 'Texas/Oil/Oil_Ports_Texas.shp'
            ]
        elif region == 'Central':
            print('Fetching Central')
            exported_files = [
                path + 'Central/Oil/Oil_PowerPlants_Cent.shp',
                path + 'Central/Oil/Oil_Terminals_Cent.shp',
                path + 'Central/Oil/Oil_Pipelines_Cent.shp',
                path + 'Central/Oil/Oil_Refined_Product_Pipelines_Cent.shp',
                path + 'Central/Oil/Oil_Refineries_Cent.shp',
                path + 'Central/Oil/Oil_Ports_Cent.shp'
            ]
        elif region == 'NE_NY':
            print('Fetching NE_NY')
            exported_files = [
                path + 'NE_NY/Oil/Oil_PowerPlants_NE_NY.shp',
                path + 'NE_NY/Oil/Oil_Terminals_NE_NY.shp',
                path + 'NE_NY/Oil/Oil_Pipelines_NE_NY.shp',
                path + 'NE_NY/Oil/Oil_Refined_Product_Pipelines_NE_NY.shp',
                path + 'NE_NY/Oil/Oil_Refineries_NE_NY.shp',
                path + 'NE_NY/Oil/Oil_Ports_NE_NY.shp'
            ]
        else:
            print('{} is not a handled region. please input: \'US\', \'TX\', \'CA\', \'NY\'')
            return
    elif energy == 'coal' or energy =='Coal':
        print('For coal:')
        if region == 'USA':
            print('Fetching US')
            exported_files = [
                path+'USA/Coal/Coal_Docks_US.shp',
                path+'USA/Coal/Coal_Sources_US.shp',
                path+'USA/Coal/Coal_Railroads_US.shp',
            ]
        elif region == 'EastCoast':
            print('Fetching EastCoast')
            exported_files = [
                path+'EastCoast/Coal/Coal_Docks_EC.shp',
                path+'EastCoast/Coal/Coal_Sources_EC.shp',
                path+'EastCoast/Coal/Coal_Railroads_EC.shp',
            ]
        elif region == 'EasternInterconnect':
            print('Fetching EasternInterconnect')
            exported_files = [
                path+'EasternInterconnect/Coal/Coal_Docks_EasternInterconnect.shp',
                path+'EasternInterconnect/Coal/Coal_Sources_EasternInterconnect.shp',
                path+'EasternInterconnect/Coal/Coal_Railroads_EasternInterconnect.shp',
            ]
        elif region == 'WestCoast':
            print('Fetching WestCoast')
            exported_files = [
                path+'WestCoast/Coal/Coal_Docks_WC.shp',
                path+'WestCoast/Coal/Coal_Sources_WC.shp',
                path+'WestCoast/Coal/Coal_Railroads_WC.shp',
            ]
        elif region == 'Texas':
            print('Fetching Texas')
            exported_files = [
                path+'Texas/Coal/Coal_Docks_Texas.shp',
                path+'Texas/Coal/Coal_Sources_Texas.shp',
                path+'Texas/Coal/Coal_Railroads_Texas.shp',
            ]
        elif region == 'Central':
            print('Fetching Central')
            exported_files = [
                path+'Central/Coal/Coal_Docks_Cent.shp',
                path+'Central/Coal/Coal_Sources_Cent.shp',
                path+'Central/Coal/Coal_Railroads_Cent.shp',
            ]
        elif region == 'NE_NY':
            print('Fetching NE_NY')
            exported_files = [
                path+'NE_NY/Coal/Coal_Docks_NE_NY.shp',
                path+'NE_NY/Coal/Coal_Sources_NE_NY.shp',
                path+'NE_NY/Coal/Coal_Railroads_NE_NY.shp',
            ]
        else:
            print('{} is not a handled region. please input: \'US\', \'TX\', \'CA\', \'NY\'')
            return
    elif energy == 'region':
        print('For region:')
        exported_files = []
        if region == 'USA':
            print('Fetching USA')
            exported_files = [
                path + 'USA/Regions/US_States.shp',
                path + 'USA/Regions/ControlAreas_USA.shp',
                path + 'USA/Regions/NG_Regions_USA.shp',
            ]
        elif region == 'NE_NY':
            print('Fetching NE_NY')
            exported_files = [
                path+'NE_NY/Regions/NE_NY_States.shp',
                path+'NE_NY/Regions/ControlAreas_NE_NY.shp',
            ]
        elif region == 'EastCoast':
            print('Fetching EastCoast')
            exported_files = [
                path + 'EastCoast/Regions/EC_States.shp',
                path + 'EastCoast/Regions/EC_ISOs.shp',
            ]
        elif region == 'EasternInterconnect':
            print('Fetching EasternInterconnect')
            exported_files = [
                path + 'EasternInterconnect/Regions/EasternInterconnect_States.shp',
                path + 'EasternInterconnect/Regions/EasternInterconnect_ISOs.shp',
            ]
        elif region == 'WestCoast':
            print('Fetching WestCoast')
            exported_files = [
                path + 'WestCoast/Regions/WC_States.shp',
                path + 'WestCoast/Regions/WC_ISOs.shp',
            ]
        elif region == 'Texas':
            print('Fetching Texas')
            exported_files = [
                path + 'Texas/Regions/Texas_States.shp',
                path + 'Texas/Regions/Texas_ISOs.shp',
            ]
        elif region == 'Central':
            print('Fetching Central')
            exported_files = [
                path + 'Central/Regions/Central_States.shp',
                path + 'Central/Regions/Central_ISOs.shp',
            ]
    else:
        print('please input an energy sector of: elec, NG, oil, coal')

    return exported_files

if __name__ == "__main__":
    """ Suggested Terminal Use: python SHP2XML.py energy1 {energy2...} region outputFile"""
    if len(sys.argv)>3:
        systems = len(sys.argv)-3
        energy = []
        for k1 in range(systems):
            energy.append(sys.argv[1+k1])
        region = sys.argv[1+systems]
        output = sys.argv[2+systems]
        AMES_SHP2XML(energy, region, output)

    else:
        print('Please Input: energy1 {energy2...} region outputFile')

