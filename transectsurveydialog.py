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
        
    def stratumLayer(self):
        comboIndex = self.mStrataLayerComboBox.currentIndex()
        strataLayerId = self.mStrataLayerComboBox.itemData( comboIndex )
        strataMapLayer = QgsProject.instance().mapLayer( strataLayerId )
        return strataMapLayer
