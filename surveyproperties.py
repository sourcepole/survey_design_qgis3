import os
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import *

FORM_CLASS = uic.loadUiType(os.path.join( os.path.dirname(__file__), 'surveypropertiesbase.ui'))[0]

class SurveyProperties( QtWidgets.QDialog, FORM_CLASS ):
    def __init__(self, parent=None):
        super(SurveyProperties, self).__init__(parent)
        self.setupUi(self)
        
    def survey(self):
        return self.mSurveyLineEdit.text()

    def projectCode(self):
        return self.mProjectCodeLineEdit.text()
        
    def date_s(self):
        return self.mDateSEdit.date().toString( 'dd/MM/yyyy' )
        
    def date_f(self):
        return self.mDateFEdit.date().toString( 'dd/MM/yyyy' )
        
    def contactName(self):
        return self.mContactNameLineEdit.text()
        
    def areas(self):
        return self.mAreasLineEdit.text()
        
    def mainspp(self):
        return self.mMainSppLineEdit.text()
        
    def comments(self):
        return self.mCommentsLIneEdit.text()
