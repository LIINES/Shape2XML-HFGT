# Shape2XML-HFGT
This software is used to take GIS shape files and create a Hetero-functional Graph Theory (HFGT) compliant XML.   The input shape files are processed, cleaned and organized into the output XML file based on the American Multi-modal Energy Systems (AMES) reference architecture.


This code was developed using Python 3.7 to execute the cleaning and processing of shape files into a HFGT compliant XML.

The code was developed using a data-driven approach relying on the AMES reference architecture and the Plats Map Data Pro data sets.  The cleaning and processing removes duplicated, canceled, retired, and improperly defined facilities, as well as clusters the nodes and edges' endpoints into unique clusters ensuring all facilities are properly connected into the system.  Based on the clustering of points, additional lines can be added to the system to connect in isolated nodes and additional independent buffers can be added to ensure every edge is connected on both ends.  After cleaning and processing the input shape files, functionality is applied other physical resources as the XML is written guided by the AMES reference architecture.

The software is run out of the script "SHP2XML.py" from the command line.  THE script is run using the following command line:

'Python SHP2XML.py {energy1 energy 2 ...} {region} {"OutputFIleName"}'

The accepted energy input can be a singular or any combination of the following operands: elec, NG, oil, coal

The accepted regions are: USA, NE_NY, EastCoast, EasternInterconnect, WestCoast, Texas, Central

