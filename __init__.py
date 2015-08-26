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
 This script initializes the plugin, making it known to QGIS and QGIS Server.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load wps4server class from file wps4server.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .wps4server import wps4server
    return wps4server(iface)
    
    
def serverClassFactory(serverIface):  # pylint: disable=invalid-name
    """Load wps4serverServer class from file wps4server.

    :param iface: A QGIS Server interface instance.
    :type iface: QgsServerInterface
    """
    #
    from .wps4server import wps4serverServer
    return wps4serverServer(serverIface)
