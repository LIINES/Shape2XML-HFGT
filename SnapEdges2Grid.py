"""
Copyright (c) 2018-2023 Laboratory for Intelligent Integrated Networks of Engineering Systems
@author: Dakota J. Thompson, Amro M. Farid
@lab: Laboratory for Intelligent Integrated Networks of Engineering Systems
@Modified: 09/29/2023
"""

import numpy as np
import scipy as sp
from scipy.spatial import distance_matrix
import scipy.sparse as sp

def snapEdges2GridRef(ptsBX, ptsBY, ptsODX, ptsODY):
    """
    snapEdges2GridRef runs a clustering algorithem to group buffers and line endpoints together.
    This connects isolated buffers with lines and lines ewithout endpoint buffers to existing buffers.

    :param ptsBX: matrix of buffer X coordinates of size buffers X refinements
    :param: ptsBY: matrix of buffer Y coordinates of size buffers X refinements
    :param: ptsODX: matrix of line origin and destination X coordinates of size lines*2 X refinements
    :param: ptsODY: matrix of line origin and destination Y coordinates of size lines*2 X refinements
    :return: clusters: A list of size # of points, designating each points cluster
    :return: clustCenters: A list of length # of clusters, designating the gps center of each cluster
    :return: pts: a list of GPS coords for each buffer and endpoint in the AMES
    :return: ptsX: a list of GPS X coordinates for each point
    :return: ptsY: a list of GPS Y coordinates for each point
    :return: resourcesToAdd: a list of lines that need to be added to the AMES designated by Origin and Destination
    """

    print('Entering snapEdges2GridRef')

    ptsX = sp.vstack((ptsODX, ptsBX))
    ptsY = sp.vstack((ptsODY, ptsBY))
    eps1 = 0.001446  # = 0.1 miles (Primary Clustering Radius)
    eps2 = 0.014465  # = 1 miles (Secondary Clustering Radius)
    eps3 = 0.5075  # = 35 miles (tertiary Clustering Radius for adding lines)
    clusters = np.array([None] * ptsX.nnz)
    clust = 0

    print('creating primary cluster')
    for k1 in range(ptsODX.shape[0]):
        lineIdx = np.where(ptsODX.row == k1)[0]
        if any(clusters[lineIdx] != None):
            continue
        for k2 in lineIdx:
            refIdx = np.where(ptsX.col == ptsODX.col[k2])[0]
            distances = ((ptsODX.data[k2]-ptsX.data[refIdx])**2 + (ptsODY.data[k2]-ptsY.data[refIdx])**2)**0.5
            found = np.where(distances <= eps1)[0]
            foundIDX = refIdx[found]
            if any(clusters[foundIDX]!=None):
                found_dist = distances[found]
                closest_clust = np.argmin(found_dist[clusters[foundIDX]!=None])
                extended_clust = clusters[foundIDX][clusters[foundIDX]!= None][closest_clust]
                clusters[foundIDX[clusters[foundIDX]== None]] = extended_clust
            else:
                clusters[foundIDX] = clust
                clust += 1

    # snap remaining isolated nodes to system
    # secondary distance for stray nodes
    print('adding secondary distance nodes')
    isoNodes = np.where(np.equal(clusters, None))[0]
    resourcesToAdd = []
    for k2 in isoNodes:
        refIdx = np.where(ptsODX.col == ptsX.col[k2])[0]
        if not refIdx.any():
            continue
        distances = ((ptsX.data[k2] - ptsODX.data[refIdx]) ** 2 + (ptsY.data[k2] - ptsODY.data[refIdx]) ** 2) ** 0.5
        nearest = np.argmin(distances)
        nearestIDX = refIdx[nearest]
        if distances[nearest] <= eps2:
            clusters[k2] = clusters[nearestIDX]
        elif distances[nearest] <= eps3:
            clusters[k2] = clust
            clust += 1
            resourcesToAdd.append((k2, nearestIDX))

    # find midpoints
    [clustCenters, pts, ptsX, ptsY] = getClustMidpointsRef(ptsX, ptsY, clusters)

    return clusters, clustCenters, pts, ptsX, ptsY, resourcesToAdd

def getClustMidpointsRef(pts_GPSX, pts_GPSY, clusters):
    """
    calculate the midpoints of each cluster of points

    :param: pts_GPSX: a list of GPS X coordinates for each point
    :param: pts_GPSY: a list of GPS Y coordinates for each point
    :param: clusters: A list of size # of points, designating each points cluster
    :return: clustCenters: A list of lenghth # of clusters, designating the gps center of each cluster
    :return: pts: a list of GPS coords for each buffer and endpoint in the AMES
    :return: ptsX: a list of GPS X coordinates for each point
    :return: ptsY: a list of GPS Y coordinates for each point
    """
    print('Entering getClustMidpointsRef')

    clusts = np.unique(clusters[~np.equal(clusters,None)])
    midpoint = np.array([(0, 0)] * len(clusters), dtype=np.float32)
    clustCenter = np.array([(0, 0)] * len(clusts), dtype=np.float32)
    for k1 in range(len(clusts)):
        clustIDX = np.where(clusters == clusts[k1])[0]
        clustCenter[k1][0] = np.mean(pts_GPSX.data[clustIDX], axis=0)
        clustCenter[k1][1] = np.mean(pts_GPSY.data[clustIDX], axis=0)
        midpoint[clustIDX] = clustCenter[k1]
        pts_GPSX.data[clustIDX] = clustCenter[k1][0]
        pts_GPSY.data[clustIDX] = clustCenter[k1][1]

    return clustCenter, midpoint, pts_GPSX, pts_GPSY
