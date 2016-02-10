
# first qgis
from qgis.core import *
from qgis.gui import *
# next Qt
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pywps import config
import os
import urllib2
import logging
import tempfile

class QGIS:

    project = None
    projectFileName = None
    outputs = None
    process = None
    sessionId = None

    def __init__(self,process,sessId):

        tmp = os.path.basename(tempfile.mkstemp()[1])
        self.outputs = {}
        self.process = process
        self.sessionId = sessId

        self.project = QgsProject.instance()

        treeRoot = self.project.layerTreeRoot()
        model = QgsLayerTreeModel(treeRoot)
        view = QgsLayerTreeView()
        view.setModel(model)
        self.canvas = QgsMapCanvas()
        self.canvas.setCrsTransformEnabled( True )
        self.bridge = QgsLayerTreeMapCanvasBridge( treeRoot, self.canvas)

        self.project.writeProject.connect( self.bridge.writeProject )
        self.project.writeProject.connect( self.__writeProject__ )

        self.projectFileName = os.path.join(config.getConfigValue("server","outputPath"),self.sessionId+".qgs")
        if os.path.exists( self.projectFileName ):
            self.project.read( QFileInfo(self.projectFileName ) )
        else:
            self.project.writePath( self.projectFileName )

        self.project.setTitle( "%s-%s"%(self.process.identifier,self.sessionId) )
        self.project.writeEntry("WMSServiceCapabilities", "/", True)
        self.project.writeEntry("WMSServiceTitle", "/", config.getConfigValue("wps","title"))
        self.project.writeEntry("WMSServiceAbstract", "/", config.getConfigValue("wps","abstract"))
        self.project.writeEntry("WMSKeywordList", "/", config.getConfigValue("wps","keywords"))
        self.project.writeEntry("WMSFees", "/", config.getConfigValue("wps","fees"))
        self.project.writeEntry("WMSAccessConstraints", "/", config.getConfigValue("wps","constraints"))
        self.project.writeEntry("WMSContactOrganization", "/", config.getConfigValue("provider","providerName"))
        self.project.writeEntry("WMSContactPerson", "/", config.getConfigValue("provider","individualName"))
        self.project.writeEntry("WMSContactPhone", "/", config.getConfigValue("provider","phoneVoice"))
        self.project.writeEntry("WMSContactPhone", "/", config.getConfigValue("provider","electronicMailAddress"))

        if config.config.has_section( 'qgis' ) and config.config.has_option( 'qgis', 'output_ows_crss' ) :
            outputOWSCRSs = config.getConfigValue( 'qgis', 'output_ows_crss' )
            outputOWSCRSs = outputOWSCRSs.split(',')
            outputOWSCRSs = [ proj.strip().upper() for proj in outputOWSCRSs ]
            self.project.writeEntry("WMSCrsList", "/", outputOWSCRSs)
        else :
            self.project.writeEntry("WMSCrsList", "/", ['EPSG:4326','EPSG:3857'])

        self.project.write( QFileInfo( self.projectFileName ) )

    def __writeProject__( self, doc ) :
        treeRoot = self.project.layerTreeRoot()
        oldLegendElem = QgsLayerTreeUtils.writeOldLegend( doc, treeRoot, False, [] )
        doc.firstChildElement( "qgis" ).appendChild( oldLegendElem )

    def getReference(self, output):

        if output.format["mimetype"] in ('text/csv', 'application/x-zipped-shp', 'application/x-zipped-tab'):
            return None

        mlr = QgsMapLayerRegistry.instance()
        logging.info('getReference: '+output.identifier+' '+output.value)
        layersByName = mlr.mapLayersByName( output.identifier )
        outputLayer = None
        if not layersByName :
            outputLayer = QgsRasterLayer( output.value, output.identifier, 'gdal' )
            if outputLayer.isValid() :
                mlr.addMapLayer( outputLayer )
            else :
                outputLayer = QgsVectorLayer( output.value, output.identifier, 'ogr' )
                mlr.addMapLayer( outputLayer )
        else :
            outputLayer = layersByName[0]

        # Update CRS
        if not outputLayer.dataProvider().crs().authid() and output.projection:
            outputLayer.setCrs( output.projection )

        treeRoot = self.project.layerTreeRoot()
        if config.config.has_section( 'qgis' ) and config.config.has_option( 'qgis', 'output_ows_crss' ) :
            outputOWSCRSs = config.getConfigValue( 'qgis', 'output_ows_crss' )
            outputOWSCRSs = outputOWSCRSs.split(',')
            outputOWSCRSs = [ proj.strip().upper() for proj in outputOWSCRSs ]
            self.canvas.setDestinationCrs( QgsCoordinateReferenceSystem( outputOWSCRSs[0] ) )
        else:
            self.canvas.setDestinationCrs( QgsCoordinateReferenceSystem( 'EPSG:4326' ) )

        if not treeRoot.findLayer( outputLayer.id() ) :
            treeRoot.addLayer( outputLayer )

        self.bridge.setCanvasLayers()
        self.canvas.zoomToFullExtent()

        self.project.write( QFileInfo( self.projectFileName ) )

        if outputLayer.type() == QgsMapLayer.VectorLayer :
            WFSLayers = self.project.readListEntry( "WFSLayers", "/" )[0]
            if outputLayer.id() not in WFSLayers :
                WFSLayers.append( outputLayer.id() )
                self.project.writeEntry( "WFSLayers", "/", WFSLayers )
                self.project.write( QFileInfo( self.projectFileName ) )
            if output.format['mimetype'] in ('application/x-ogc-wms', 'application/x-ogc-wfs'):
                return self.getCapabilities(output)
            return self.getMapServerWFS(output)

        elif outputLayer.type() == QgsMapLayer.RasterLayer :
            output.projection = outputLayer.crs().authid()
            output.height = outputLayer.height()
            output.width = outputLayer.width()
            outputExtent = outputLayer.extent()
            output.bbox = [outputExtent.xMinimum(), outputExtent.yMinimum(), outputExtent.xMaximum(), outputExtent.yMaximum()]
            WCSLayers = self.project.readListEntry( "WCSLayers", "/" )[0]
            if outputLayer.id() not in WCSLayers :
                WCSLayers.append( outputLayer.id() )
                self.project.writeEntry( "WCSLayers", "/", WCSLayers )
                self.project.write( QFileInfo( self.projectFileName ) )
            if output.format['mimetype'] in ('application/x-ogc-wms', 'application/x-ogc-wcs'):
                return self.getCapabilities(output)
            return self.getMapServerWCS(output)

    def getCapabilities(self,output):
        """Get the URL for qgis-server GetCapapbilities request of the output"""
        if output.format["mimetype"] == 'application/x-ogc-wms':
            return config.getConfigValue("qgis","qgisserveraddress")+"?map="+self.projectFileName+"&SERVICE=WMS"+ "&REQUEST=GetCapabilities"
        elif output.format["mimetype"] == 'application/x-ogc-wfs':
            return config.getConfigValue("qgis","qgisserveraddress")+"?map="+self.projectFileName+"&SERVICE=WFS"+ "&REQUEST=GetCapabilities"
        elif output.format["mimetype"] == 'application/x-ogc-wcs':
            return config.getConfigValue("qgis","qgisserveraddress")+"?map="+self.projectFileName+"&SERVICE=WCS"+ "&REQUEST=GetCapabilities"
        else:
            return config.getConfigValue("qgis","qgisserveraddress")+"?map="+self.projectFileName+"&SERVICE=WMS"+ "&REQUEST=GetCapabilities"

    def getMapServerWCS(self,output):
        """Get the URL for qgis-server WCS request of the output"""
        return config.getConfigValue("qgis","qgisserveraddress")+ "?map="+self.projectFileName+ "&SERVICE=WCS"+ "&REQUEST=GetCoverage"+ "&VERSION=1.0.0"+ "&COVERAGE="+output.identifier+"&CRS="+output.projection.replace("+init=","")+ ("&BBOX=%s,%s,%s,%s"%(output.bbox[0],output.bbox[1],output.bbox[2],output.bbox[3]))+ "&HEIGHT=%s" %(output.height)+("&WIDTH=%s"%(output.width))+("&FORMAT=%s"%output.format["mimetype"])

    def getMapServerWFS(self,output):
        """Get the URL for qgis-server WFS request of the output"""
        url = config.getConfigValue("qgis","qgisserveraddress")+"?map="+self.projectFileName+"&SERVICE=WFS"+ "&REQUEST=GetFeature"+ "&VERSION=1.0.0"+"&TYPENAME="+output.identifier
        if output.format["mimetype"] == 'application/json' :
            url+= "&OUTPUTFORMAT=GeoJSON"
        elif output.format["mimetype"] in ('text/xml; subtype=gml/3.1.1','application/gml+xml; version=3.1.1') :
            url+= "&OUTPUTFORMAT=GML3"
        else :
            url+= "&OUTPUTFORMAT=GML2"
        return url;
