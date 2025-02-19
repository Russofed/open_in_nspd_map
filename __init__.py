# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenNSPDMap
                                 A QGIS plugin
 Opens the current map extent in NSPD map
                              -------------------
        begin                : 2025-02-19
        copyright            : (C) 2025 Alexandr Fedorov
        email                : russouj@gmail.com
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

Initialises the plugin

###

"""

# Import plugin
def classFactory(iface):
    from .open_in_nspd_map import OpenInNSPDMapPlugin
    return OpenInNSPDMapPlugin(iface)
