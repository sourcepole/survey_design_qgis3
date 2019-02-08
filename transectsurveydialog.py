# -*- coding: utf-8 -*-

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog

from qgis.core import *
from qgis.gui import *
from .surveyutils import *
from .transectsample import *
from .surveyproperties import *

from .xlsxwriter import *

FORM_CLASS = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'transectsurveydialogbase.ui'))[0]

class TransectSurveyDialog( QtWidgets.QDialog, FORM_CLASS ):
    def __init__(self, iface, parent=None):
        super(TransectSurveyDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        
        fillLayerComboBox( self.mSurveyAreaLayerComboBox,  QgsWkbTypes.PolygonGeometry,  True )
        fillLayerComboBox( self.mStrataLayerComboBox,  QgsWkbTypes.PolygonGeometry,  False )
        fillLayerComboBox( self.mSurveyBaselineLayerComboBox,  QgsWkbTypes.LineGeometry,  False )
        
        self.strataLayerComboBoxChanged()
        
        self.mCreateSampleButton.clicked.connect( self.createSample )
        
    def strataLayerComboBoxChanged( self ):
        comboIndex = self.mStrataLayerComboBox.currentIndex()
        if comboIndex is None:
            return
        layerId = self.mStrataLayerComboBox.itemData( comboIndex )
        layer = QgsProject.instance().mapLayer( layerId )
        if layer is None:
            return
        
        fillAttributeComboBox( self.mMinimumDistanceAttributeComboBox,  layer )
        fillAttributeComboBox( self.mNSamplePointsComboBox,  layer )
        fillAttributeComboBox( self.mStrataIdAttributeComboBox,  layer )
        
    def createSample( self ):
        
        #survey properties
        surveyProps = SurveyProperties( self )
        if surveyProps.exec_() == QDialog.Rejected:
            return
        
        #save dir
        fileDialog = QFileDialog(  self,  QCoreApplication.translate( 'SurveyDesignDialog', 'Select output directory for result files' )  )
        fileDialog.setFileMode( QFileDialog.Directory )
        fileDialog.setOption( QFileDialog.ShowDirsOnly )
        if fileDialog.exec_() != QDialog.Accepted:
            return
        saveDir = fileDialog.selectedFiles()[0]
        
        outputPointShape = saveDir + '/transect_points.shp' 
        outputLineShape = saveDir + '/transect_lines.shp' 
        usedBaselineShape = saveDir + '/used_baselines.shp'
        
       #strata map layer
        strataMapLayer = self.stratumLayer()
        if strataMapLayer is None:
            return
            
        strataMinDistance = self.mMinimumDistanceAttributeComboBox.currentText()
        strataNSamplePoints = self.mNSamplePointsComboBox.currentText()
        strataId = self.mStrataIdAttributeComboBox.currentText()
            
        #baseline map layer
        comboIndex = self.mSurveyBaselineLayerComboBox.currentIndex()
        baselineLayerId = self.mSurveyBaselineLayerComboBox.itemData( comboIndex )
        baselineMapLayer = QgsProject.instance().mapLayer( baselineLayerId )
        
        #assume everything is in stratum units
        minDistanceUnits = TransectDistanceUnits.StrataUnits
        
        transectSample = TransectSample(  strataMapLayer, strataId , strataMinDistance, strataNSamplePoints, minDistanceUnits, baselineMapLayer, True,
        '', outputPointShape, outputLineShape,  usedBaselineShape,  self.mMinimumTransectLengthSpinBox.value(),  -1.0,  -1.0 )
        transectSample.createSample()
        
        #open line shape and create a dict station_id / bearing
        #first find out 'station_co' attribute name
        transectLineLayer = QgsVectorLayer( outputLineShape,  'transectLineLayer',  'ogr' )
        fields = transectLineLayer.fields()
        stationCodeFieldName = "station_co"
        for field in fields:
            if field.name().startswith( "station_co" ):
                stationCodeFieldName = field.name()
                break
        
        bearingDict = {}
        
        transectLineIt = transectLineLayer.getFeatures()
        for transectLineFeature in transectLineIt:
            station_co = transectLineFeature.attribute( stationCodeFieldName )
            bearing = transectLineFeature.attribute( 'bearing' )
            bearingDict[station_co] = bearing
            
        #write bearing into output point shape
        transectPointLayer = QgsVectorLayer( outputPointShape,  'transectPointLayer',  'ogr' )
        transectPointLayer.startEditing()
        transectPointLayer.addAttribute( QgsField( 'bearing',  QVariant.Double,  "Double" ) )
        bearingIndex = transectPointLayer.fields().indexFromName( 'bearing' )
        transectPointIt = transectPointLayer.getFeatures()
        for transectPointFeature in transectPointIt:
            station_co = transectPointFeature.attribute( stationCodeFieldName )
            transectPointLayer.changeAttributeValue( transectPointFeature.id(),  bearingIndex,  bearingDict[ station_co] )
        transectPointLayer.commitChanges()
        
        #write gpx file
        gpxFileInfo = QFileInfo( outputPointShape )
        gpxFileName = gpxFileInfo.path() + '/' + gpxFileInfo.baseName() + '.gpx'
        writePointShapeAsGPX( outputPointShape,  stationCodeFieldName, 'bearing',   gpxFileName )
        
        transectLayer = QgsVectorLayer( outputLineShape,  "transect",  "ogr" )
        
        #write XLSX output
        workbook = Workbook( saveDir + '/survey.xlsx')
        writeSurveyXLSX( workbook, surveyProps.survey(),  surveyProps.projectCode(), surveyProps.date_s() , surveyProps.date_f(),  surveyProps.contactName(),  surveyProps.areas(), surveyProps.mainspp(),  surveyProps.comments() )
        writeStationXLSX( workbook, transectLayer, "stratum_id",  "station_id",  surveyProps.survey() )
        writeStratumXLSX( workbook, self.stratumLayer(), self.mStrataIdAttributeComboBox.currentText(),  surveyProps.survey() )
        writeStratumBoundaryXLSX( workbook, self.stratumLayer(), self.mStrataIdAttributeComboBox.currentText(),  surveyProps.survey() )
        writeCatchXLSX( workbook )
        writeLengthXLSX( workbook )
        workbook.close()
        
        #write csv files
        #Survey.csv
        writeSurveyCSV( fileDialog.selectedFiles()[0],  surveyProps.survey(),  surveyProps.projectCode(), surveyProps.date_s() , surveyProps.date_f(),  surveyProps.contactName(),  surveyProps.areas(), surveyProps.mainspp(),  surveyProps.comments() )
        writeStationCSV( saveDir,  transectLayer, "stratum_id",  "station_id",  surveyProps.survey() )
        writeStratumCSV( fileDialog.selectedFiles()[0], self.stratumLayer(), self.mStrataIdAttributeComboBox.currentText(),  surveyProps.survey() )
        writeStratumBoundaryCSV( fileDialog.selectedFiles()[0], self.stratumLayer(), self.mStrataIdAttributeComboBox.currentText(),  surveyProps.survey() )
        writeCatchCSV( saveDir )
        writeLengthCSV( saveDir )
        
        self.iface.addVectorLayer( outputLineShape, 'transects', 'ogr' )
        self.iface.addVectorLayer( outputPointShape,  'transect_stations',  'ogr' )
        
    def stratumLayer(self):
        comboIndex = self.mStrataLayerComboBox.currentIndex()
        strataLayerId = self.mStrataLayerComboBox.itemData( comboIndex )
        strataMapLayer = QgsProject.instance().mapLayer( strataLayerId )
        return strataMapLayer
