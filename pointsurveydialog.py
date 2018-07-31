# -*- coding: utf-8 -*-

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import *

from qgis.core import *
from qgis.gui import *

from .pointsample import PointSample
from .surveyutils import fillLayerComboBox
from .surveyutils import fillAttributeComboBox

FORM_CLASS = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'pointsurveydialogbase.ui'))[0]

class PointSurveyDialog( QtWidgets.QDialog, FORM_CLASS ):
    def __init__(self, iface, parent=None):
        super(PointSurveyDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        
        fillLayerComboBox( self.mSurveyAreaLayerComboBox,  QgsWkbTypes.PolygonGeometry,  True )
        fillLayerComboBox( self.mStrataLayerComboBox,  QgsWkbTypes.PolygonGeometry,  False )
        self.strataLayerComboBoxChanged()
        
        self.mStrataLayerComboBox.currentIndexChanged.connect( self.strataLayerComboBoxChanged )
        self.mCreateSampleButton.clicked.connect( self.createSample )
        
    def strataLayerComboBoxChanged(self):
        comboIndex = self.mStrataLayerComboBox.currentIndex()
        if comboIndex is None:
            return
        layerId = self.mStrataLayerComboBox.itemData( comboIndex )
        layer = QgsProject.instance().mapLayer( layerId )
        if layer is None:
            return
            
        fillAttributeComboBox( self.mMinimumDistanceAttributeComboBox,  layer )
        fillAttributeComboBox( self.mNSamplePointsComboBox,  layer )
        fillAttributeComboBox( self.mStrataIdComboBox,  layer )
    
    def createSample( self ):
        fileDialog = QFileDialog(  self,  QCoreApplication.translate( 'SurveyDesignDialog', 'Select output directory for result files' )  )
        fileDialog.setFileMode( QFileDialog.Directory )
        fileDialog.setOption( QFileDialog.ShowDirsOnly )
        if fileDialog.exec_() != QDialog.Accepted:
            return
            
        saveDir = fileDialog.selectedFiles()[0]
        
        comboIndex = self.mStrataLayerComboBox.currentIndex()
        strataLayerId = self.mStrataLayerComboBox.itemData( comboIndex )
        strataLayer = QgsProject.instance().mapLayer( strataLayerId )
        if strataLayer is None:
            return
            
        minDistanceAttribute = self.mMinimumDistanceAttributeComboBox.currentText()
        nSamplePointsAttribute = self.mNSamplePointsComboBox.currentText()
        
        if len( minDistanceAttribute ) == 0 or len( nSamplePointsAttribute ) == 0:
            return

        outputShape =  saveDir + "/point_sample.shp"

        p = PointSample (  strataLayer, outputShape, nSamplePointsAttribute, minDistanceAttribute )
        p.createRandomPoints()
