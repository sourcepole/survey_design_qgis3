from qgis.core import QgsMapLayer
from qgis.core import QgsProject
from qgis.core import QgsVectorLayer
from PyQt5.QtWidgets import QComboBox

def fillLayerComboBox( comboBox,  geometryType,  noneEntry ):
    comboBox.clear()
    if noneEntry == True:
        comboBox.addItem( comboBox.tr( 'None' ) )

    mapLayers = QgsProject.instance().mapLayers()
    for id in mapLayers:
        currentLayer = mapLayers[id]
        if currentLayer.type() != QgsMapLayer.VectorLayer:
            continue

        if currentLayer.geometryType() == geometryType:
            comboBox.addItem( currentLayer.name(), currentLayer.id() )
            
def fillAttributeComboBox( comboBox,  vectorLayer ):
    comboBox.clear()
    if not vectorLayer is None:
        if not vectorLayer.type() == QgsMapLayer.VectorLayer:
            return

        fieldList = vectorLayer.fields().toList()
        for field in fieldList:
            comboBox.addItem( field.name() )
