from PyQt5.QtWidgets import QAction, QMenu
from PyQt5.QtCore import QCoreApplication, QObject
from .pointsurveydialog import PointSurveyDialog
from .transectsurveydialog import TransectSurveyDialog

class SurveyDesignPlugin:
    def __init__( self, iface ):
        self.iface = iface

    def initGui(self):
        menuBar = self.iface.mainWindow().menuBar()
        surveyDesignMenu = QMenu( QCoreApplication.translate("SurveyDesignPlugin","Survey") ,  menuBar)

        self.actionTransectSurvey = QAction( 'Transect survey',  self.iface.mainWindow() )
        self.actionTransectSurvey.triggered.connect( self.transectSurvey )
        self.actionPointSurvey = QAction( 'Point survey',  self.iface.mainWindow() )
        self.actionPointSurvey.triggered.connect( self.pointSurvey )

        surveyDesignMenu.addAction( self.actionTransectSurvey )
        surveyDesignMenu.addAction( self.actionPointSurvey )
        self.surveyDesignAction = menuBar.addMenu( surveyDesignMenu )

    def unload(self):
        self.iface.mainWindow().menuBar().removeAction( self.surveyDesignAction )

    def transectSurvey(self):
        self.transectSurveyDialog = TransectSurveyDialog( self.iface, self.iface.mainWindow() )
        self.transectSurveyDialog.show()

    def pointSurvey(self):
        self.pointSurveyDialog = PointSurveyDialog( self.iface, self.iface.mainWindow() )
        self.pointSurveyDialog.show()
