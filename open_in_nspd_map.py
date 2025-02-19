# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenNSPDMap
                                 A QGIS plugin
 Opens the current map extent in NSPD map
                              -------------------
        begin                : 2024-12-17
        copyright            : (C) 2024 Harry King
        email                : nlu1vwm0@anonaddy.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

###

Core plugin code

###
"""

# Import Packages - QGIS
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, Qgis

# Import Packages - General
import os
import webbrowser

class OpenInNSPDMapPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.action = QAction(QIcon(icon_path), 'Open in NSPD Map', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        self.iface.addToolBarIcon(self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
            self.iface.mainWindow().removeAction(action)
        self.actions.clear()

    def run(self):
        canvas = self.iface.mapCanvas()
        extent = canvas.extent()
        current_crs = canvas.mapSettings().destinationCrs()
        target_crs = QgsCoordinateReferenceSystem('EPSG:3857')
        transform = QgsCoordinateTransform(current_crs, target_crs, QgsProject.instance())
        transformed_extent = transform.transformBoundingBox(extent)
        
        center_x = (transformed_extent.xMinimum() + transformed_extent.xMaximum()) / 2
        center_y = (transformed_extent.yMinimum() + transformed_extent.yMaximum()) / 2
        zoom = self._calculate_zoom_level()
        
        nspd_url = f"https://nspd.gov.ru/map?zoom={zoom}&coordinate_x={center_x}&coordinate_y={center_y}&theme_id=1&is_copy_url=true"
        
        webbrowser.open(nspd_url)

    def _calculate_zoom_level(self):
        canvas = self.iface.mapCanvas()
        scale = canvas.scale()
        
        if scale < 100: return 20
        elif scale < 250: return 19
        elif scale < 500: return 18
        elif scale < 1000: return 17
        elif scale < 2500: return 16
        elif scale < 5000: return 15
        elif scale < 10000: return 14
        elif scale < 25000: return 13
        elif scale < 50000: return 12
        elif scale < 100000: return 11
        elif scale < 250000: return 10
        elif scale < 500000: return 9
        elif scale < 1000000: return 8
        elif scale < 2500000: return 7
        elif scale < 5000000: return 6
        elif scale < 10000000: return 5
        elif scale < 25000000: return 4
        elif scale < 50000000: return 3
        else: return 2
