# -*- coding: utf-8 -*-

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import *

from qgis.core import *
from qgis.gui import *
from .surveyutils import *

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
        print( 'Creating Sample' )
