from qgis.core import *
from PyQt5.QtCore import QVariant
import random

class PointSample:
    def __init__( self, inputLayer, outputLayerFile, nPointsAttribute, minDistAttribute ):
        self.inputLayer = inputLayer
        self.outputLayerFile = outputLayerFile
        self.nPointsAttribute = nPointsAttribute
        self.minDistAttribute = minDistAttribute
        self.nCreatedPoints = 0
        
    def createRandomPoints( self ):
        
        if self.inputLayer is None:
            return False

        if self.inputLayer.geometryType() != QgsWkbTypes.PolygonGeometry:
            return False
        
        self.nCreatedPoints = 0
        
        outputFields = QgsFields()
        outputFields.append( QgsField( 'id', QVariant.Int ) )
        outputFields.append( QgsField( 'station_id', QVariant.Int ) )
        outputFields.append( QgsField( 'stratum_id', QVariant.Int ) )
        writer  = QgsVectorFileWriter( self.outputLayerFile, 'UTF-8', outputFields, QgsWkbTypes.Point, self.inputLayer.crs(), 'ESRI Shapefile' )
        if writer.hasError() != QgsVectorFileWriter.NoError:
            return False
        
        fReq = QgsFeatureRequest()
        attributeSubset = [ self.nPointsAttribute, self.minDistAttribute ]
        fReq.setSubsetOfAttributes( attributeSubset, self.inputLayer.fields() )
        features = self.inputLayer.getFeatures( fReq )
        for f in  features:
            nPoints = int( f.attribute( self.nPointsAttribute ) )
            minDistance = -1
            if self.minDistAttribute:
                minDistance = float(f.attribute( self.minDistAttribute ) )
            self.addSamplePoints( f, writer, outputFields, nPoints, minDistance )
        
        return True
    
    def addSamplePoints( self, fet, writer, outputFields, nPoints, minDistance ):
        
        geometry = fet.geometry()
        if geometry is None:
            return
        bbox = geometry.boundingBox()
        if bbox.isEmpty():
            return
        
        sIndex = QgsSpatialIndex()
        pointMapForFeatures = {} #feature id / QgsPoint
        
        nIterations = 0
        maxIterations = nPoints * 200
        points = 0
        
        randX = 0.0
        randY = 0.0
        
        random.seed()
        
        while ( nIterations < maxIterations and points < nPoints ):
            randX = random.random() * bbox.width() + bbox.xMinimum()
            randY = random.random() * bbox.height() + bbox.yMinimum()
            randomPoint = QgsPoint( randX, randY )
            randomPointGeom = QgsGeometry.fromPointXY( QgsPointXY( randomPoint.x(), randomPoint.y() ) )
            if randomPointGeom.within( geometry ) and self.checkMinDistance( randomPoint, sIndex, minDistance, pointMapForFeatures ):
                f = QgsFeature( outputFields, self.nCreatedPoints )
                f.setAttribute( 'id', self.nCreatedPoints )
                f.setAttribute( 'station_id', points + 1 )
                f.setAttribute( 'stratum_id', fet.id() )
                f.setGeometry(  randomPointGeom )
                writer.addFeature( f )
                sIndex.insertFeature( f )
                pointMapForFeatures[self.nCreatedPoints] = randomPoint
                points += 1
                self.nCreatedPoints += 1
            nIterations += 1
            
    def checkMinDistance( self, pt, spatialIndex, minDistance, pointMap ):
        if minDistance < 0:
            return True
        
        neighborList = spatialIndex.nearestNeighbor( QgsPointXY( pt.x(), pt.y() ), 1 )
        print('neighbor List:')
        print( neighborList )
        if len( neighborList ) < 1:
            return True
        
        if not neighborList[0] in pointMap:
            return True
        
        neighborPoint = pointMap[neighborList[0]]
        if pt.distance( neighborPoint ) < minDistance:
            return False
        
        return True
