# -*- coding: utf-8 -*-

import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import *

from qgis.core import *
from qgis.gui import *

FORM_CLASS = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'pointsurveydialogbase.ui'))[0]

class PointSurveyDialog( QtWidgets.QDialog, FORM_CLASS ):
    def __init__(self, iface, parent=None):
        super(PointSurveyDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
