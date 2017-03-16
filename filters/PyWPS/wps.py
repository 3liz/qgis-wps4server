#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
This program is simple implementation of OGC's [http://opengeospatial.org]
Web Processing Service (OpenGIS(r) Web Processing Service - OGC 05-007r7)
version 1.0.0 from 2007-06-08

Target of this application is to bring functionality of GIS GRASS
[http://grass.osgeo.it] to the World Wide Web - it should work like
wrapper for modules of this GIS. Though GRASS was at the first place in the
focus, it is not necessary to use it's modules - you can use any program
you can script in Python or other language.

This first version was written with support of Deutsche Bundesstiftung
Umwelt, Osnabrueck, Germany on the spring 2006. SVN server was hosted by
GDF-Hannover, Hannover, Germany; today at Intevation GmbH, Germany.

Current development is supported mainly by:
Help Service - Remote Sensing s.r.o
Cernoleska 1600
256  01 - Benesov u Prahy
Czech Republic
Europe

For setting see comments in 'etc' directory and documentation.

This program is free software, distributed under the terms of GNU General
Public License as published by the Free Software Foundation version 2 of the
License.

Enjoy and happy GISing!
"""
__version__ = "3.2.2"


# Author:    Jachym Cepicky
#            http://les-ejk.cz
# License:
#
# Web Processing Service implementation
# Copyright (C) 2006 Jachym Cepicky
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA


# first qgis
from qgis.core import *
# next Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import pywps
from pywps import config
from pywps.Exceptions import *

import sys
import os
import traceback
import inspect

# get the request method and inputs
method = os.getenv("REQUEST_METHOD")
if not method:  # set standard method
    method = pywps.METHOD_GET

inputQuery = None
if method == pywps.METHOD_GET:
    try:
        inputQuery = os.environ["QUERY_STRING"]
    except KeyError:
        # if QUERY_STRING isn't found in env-dictionary, try to read
        # query from command line:
        if len(sys.argv) > 1:  # any arguments available?
            inputQuery = sys.argv[1]
    if not inputQuery:
        err = NoApplicableCode("No query string found.")
        pywps.response.response(err, sys.stdout)
        sys.exit(1)
else:
    inputQuery = sys.stdin

# create the WPS object
wps = None
try:
    # Get or define user_folder
    config.loadConfiguration()
    user_folder = os.path.dirname(os.path.abspath(
        inspect.getfile(inspect.currentframe())))
    if config.config.has_option('qgis', 'user_folder'):
        user_folder = config.getConfigValue('qgis', 'user_folder')

    # init QgsApplication
    QgsApplication(sys.argv, False, user_folder)
    # supply path to where is your qgis installed
    QgsApplication.setPrefixPath(config.getConfigValue("qgis", "prefix"), True)

    # load providers
    QgsApplication.initQgis()

    # initialize application
    qa = QApplication(sys.argv)
    wps = pywps.Pywps(method)
    if wps.parseRequest(inputQuery):
        pywps.debug(wps.inputs)
        response = wps.performRequest()
        # request performed, write the response back
        if response:
            # print only to standard out
            pywps.response.response(wps.response,
                                    sys.stdout, wps.parser.soapVersion, wps.parser.isSoap, wps.parser.isSoapExecute, wps.request.contentType)
    QgsApplication.exitQgis()
    qa.exit()

except WPSException, e:
    traceback.print_exc(file=pywps.logFile)
    pywps.response.response(e, sys.stdout, wps.parser.soapVersion,
                            wps.parser.isSoap,
                            wps.parser.isSoapExecute)
