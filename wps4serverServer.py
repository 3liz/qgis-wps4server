# -*- coding: utf-8 -*-
"""
/***************************************************************************
    wps4server: A QGIS Server plugin to add OGC Web Processing Service
     capabilities
    ---------------------
    Date                 : August 2015
    copyright            : (C) 2015 by DHONT René-Luc - 3Liz
    email                : rldhont@3liz.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'DHONT René-Luc'
__date__ = 'August 2015'
__copyright__ = '(C) 2015, DHONT René-Luc - 3Liz'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.server import *

import os.path

class wps4serverServer:
    """Plugin for QGIS server
    this plugin loads wps filter based on PyWPS"""

    def __init__(self, serverIface):
        # Save reference to the QGIS server interface
        self.serverIface = serverIface
        QgsMessageLog.logMessage("SUCCESS - wps4server init", 'plugin', QgsMessageLog.INFO)
        
        from filters.wpsFilter import wpsFilter
        try:
            serverIface.registerFilter( wpsFilter(serverIface), 100 )
        except Exception, e:
            QgsLogger.debug("wps4server - Error loading filter wps : %s" % e )

