from qgis.core import *
from PyQt5.QtCore import *
from enum import Enum
import math
import random
import sys

class TransectDistanceUnits(Enum):
    Meters = 1
    StrataUnits = 2

class TransectSample:
    def __init__( self,  stratumLayer,  stratumIdAttribute,  minDistAttribute,  nPointsAttribute,  minDistUnits,  baselineLayer,  shareBaseline,  
   baselineStratumId,  outputPointLayer,  outputLineLayer,  usedBaselineLayer,  minTransectLength = 0.0,  baselineBufferDistance = -1.0,  
   baselineSimplificationTolerance = -1.0 ):
        self.stratumLayer = stratumLayer
        self.stratumIdAttribute = stratumIdAttribute
        self.minDistAttribute = minDistAttribute
        self.nPointsAttribute = nPointsAttribute
        self.minDistUnits = minDistUnits
        self.baselineLayer = baselineLayer
        self.shareBaseline = shareBaseline
        self.baselineStratumId = baselineStratumId
        self.outputPointLayer = outputPointLayer
        self.outputLineLayer = outputLineLayer
        self.usedBaselineLayer = usedBaselineLayer
        self.minTransectLength = minTransectLength
        self.baselineBufferDistance = baselineBufferDistance
        self.baselineSimplificationTolerance = baselineSimplificationTolerance
        
    def createSample( self ):
        if self.stratumLayer is None or self.baselineLayer is None:
            return
            
        stratumIdType = QVariant.Int;
        if self.stratumIdAttribute:
            stratumIdType = self.stratumLayer.fields().field( self.stratumIdAttribute ).type()
            
        #File writer for transect start points
        outputPointFields = QgsFields()
        outputPointFields.append( QgsField( 'id',  stratumIdType ) )
        outputPointFields.append( QgsField( 'station_id',  QVariant.Int ) )
        outputPointFields.append( QgsField( 'stratum_id',  stratumIdType ) )
        outputPointFields.append( QgsField( 'station_code',  QVariant.String ) )
        outputPointFields.append( QgsField( 'start_lat',  QVariant.Double ) )
        outputPointFields.append( QgsField( 'start_long',  QVariant.Double ) )
        outputPointWriter = QgsVectorFileWriter( self.outputPointLayer,  'utf-8',  outputPointFields, QgsWkbTypes.Point,  self.stratumLayer.crs(), 'ESRI Shapefile'  )
        
        outputPointFields.append( QgsField( 'bearing',  QVariant.Double ) )
        outputLineWriter = QgsVectorFileWriter( self.outputLineLayer,  'utf-8',  outputPointFields,  QgsWkbTypes.LineString,  self.stratumLayer.crs(),  'ESRI Shapefile' )
        distanceArea = QgsDistanceArea()
        distanceArea.setSourceCrs( self.stratumLayer.crs(),  QgsProject.instance().transformContext() )
        
        toLatLongTransform = QgsCoordinateTransform( self.stratumLayer.crs(),  QgsCoordinateReferenceSystem( 4326,  QgsCoordinateReferenceSystem.EpsgCrsId ),  QgsProject.instance().transformContext() )
        
        #loop over stratum features
        fr = QgsFeatureRequest()
        fr.setSubsetOfAttributes( [ self.stratumIdAttribute,  self.minDistAttribute,  self.nPointsAttribute ],  self.stratumLayer.fields() )
        stratumFeatures = self.stratumLayer.getFeatures( fr )
        
        #init random number generator
        random.seed()
        
        nTotalTransects = 0
        nFeatures = 0
        for f in stratumFeatures:
            stratumGeom = f.geometry()
            if stratumGeom is None:
                continue
            
            stratumId = f.attribute( self.stratumIdAttribute )
            baselineGeom = None
            if isinstance(stratumId, int):
                baselineGeom = self.findBaselineGeometry( stratumId )
            else:
                baselineGeom = self.findBaselineGeometry( -1 )
                
            if baselineGeom is None:
                continue
            
            minDistance = f.attribute( self.minDistAttribute )
            minDistanceLayerUnits = minDistance
            bufferDist = self.bufferDistance( minDistance )
            if self.minDistUnits == TransectDistanceUnits.Meters and self.stratumLayer.crs().mapUnits() == QgsUnitTypes.DistanceDegrees:
                minDistanceLayerUnits = minDistance / 111319.9
                
            clippedBaseline = stratumGeom.intersection( baselineGeom )
            if clippedBaseline is None:
                continue
            
            #Make sure clippedBaseLine is not a geometry collection
            if QgsWkbTypes.flatType( clippedBaseline.wkbType() ) == QgsWkbTypes.GeometryCollection:
                clippedBaseline.convertGeometryCollectionToSubclass( QgsWkbTypes.LineGeometry )
            
            bufferLineClipped = self.clipBufferLine( stratumGeom, clippedBaseline, bufferDist )
            if bufferLineClipped is None:
                print( '**bufferLineClipped is None**' )
                continue
            
            
            
            nTransects = f.attribute( self.nPointsAttribute )
            print( '*nTransects*' )
            print( nTransects )
            nCreatedTransects = 0
            nIterations = 0
            nMaxIterations = nTransects * 50
            
            sIndex = QgsSpatialIndex()
            lineFeatureDict = {}
            
            while nCreatedTransects < nTransects and nIterations < nMaxIterations:
                print ('****************Create Transect*******************')
                print( clippedBaseline )
                
                randomPosition = random.random() * clippedBaseline.length()
                print( randomPosition )
                samplePoint = clippedBaseline.interpolate( randomPosition )
                print( samplePoint )
                nIterations += 1
                
                if samplePoint is None or samplePoint.isNull():
                    continue
                
                samplePointXY = samplePoint.asPoint()
                latLongPointXY = toLatLongTransform.transform( samplePointXY )
                
                samplePointFeature = QgsFeature( outputPointFields )
                samplePointFeature.setGeometry( samplePoint )
                samplePointFeature.setAttribute( "id", nTotalTransects + 1 )
                samplePointFeature.setAttribute( "station_id", nCreatedTransects + 1 )
                samplePointFeature.setAttribute( "stratum_id", stratumId )
                samplePointFeature.setAttribute( "station_code", str( stratumId ) + '_' + str( nCreatedTransects + 1 ) )
                samplePointFeature.setAttribute( "start_lat", latLongPointXY.y() )
                samplePointFeature.setAttribute( "start_long", latLongPointXY.x() )
                
                #find closest point on clipped buffer line
                snapResult = bufferLineClipped.closestSegmentWithContext( samplePointXY )
                if snapResult[0] < 0:
                    continue
                
                minDistPoint = snapResult[1]
                
                #bearing between sample point and min dist point (transect direction)
                bearing = distanceArea.bearing( samplePointXY, minDistPoint ) / math.pi * 180.0
                
                ptFarAway = QgsPointXY( samplePointXY.x() + ( minDistPoint.x() - samplePointXY.x() ) * 1000000,
                                       samplePointXY.y() + ( minDistPoint.y() - samplePointXY.y() ) * 1000000 )
                
                lineFarAway = QgsGeometry.fromPolylineXY( [samplePointXY, ptFarAway] );
                lineClipStratum = lineFarAway.intersection( stratumGeom )
                if lineClipStratum is None:
                    continue
                
                
                #cancel if distance between sample point and line is too large (line does not start at point)
                if lineClipStratum.distance( samplePoint ) > 0.000001:
                    continue
                
                #if lineClipStratum is a multiline, take the part line closest to samplePoint
                '''if QgsWkbTypes.flatType( lineClipStratum.wkbType() ) == QgsWkbTypes.MultiLineString:
                    singleLine = self.closestMultilineElement( samplePoint, lineClipStratum )
                    if singleLine:
                        lineClipStratum = singleLine'''
                
                #cancel if length of lineClipStratum is too small
                transectLength = distanceArea.measureLength( lineClipStratum )
                if transectLength < self.minTransectLength:
                    continue
                
                #search closest existing profile. Cancel if dist < minDist
                if self.otherTransectWithinDistance( lineClipStratum, minDistanceLayerUnits, minDistance, sIndex, lineFeatureDict, distanceArea ):
                    continue
                
                sampleLineFeature = QgsFeature( outputPointFields, nCreatedTransects )
                sampleLineFeature.setGeometry( lineClipStratum )
                sampleLineFeature.setAttribute( 'id', nTotalTransects + 1 )
                sampleLineFeature.setAttribute( 'station_id', nCreatedTransects + 1 )
                sampleLineFeature.setAttribute( 'stratum_id', stratumId )
                sampleLineFeature.setAttribute( 'station_code', str( stratumId ) + '_' + str( nCreatedTransects + 1 ) )
                sampleLineFeature.setAttribute( 'start_lat', latLongPointXY.y() );
                sampleLineFeature.setAttribute( 'start_long', latLongPointXY.x() );
                sampleLineFeature.setAttribute( 'bearing', bearing );
                outputLineWriter.addFeature( sampleLineFeature )
                
                #Add point to file writer here. It can only be written if the corresponding transect has been as well
                outputPointWriter.addFeature( samplePointFeature );
                
                sIndex.insertFeature( sampleLineFeature )
                lineFeatureDict[ nCreatedTransects ] = sampleLineFeature.geometry()
                
                nTotalTransects += 1
                nCreatedTransects += 1
    
    def clipBufferLine( self, stratumGeom, clippedBaseline, tolerance ):
        if stratumGeom is None or clippedBaseline is None or clippedBaseline.wkbType() == QgsWkbTypes.Unknown:
            return None
        
        usedBaseline = clippedBaseline
        if  self.baselineSimplificationTolerance >= 0:
            usedBaseline = clippedBaseline.simplify( self.baselineSimplificationTolerance )
            if usedBaseline is None:
                return None
            
        currentBufferDist = tolerance
        maxLoops = 10
        
        for i in range(0, maxLoops):
            clipBaselineBuffer = usedBaseline.buffer( currentBufferDist, 8 )
            if clipBaselineBuffer is None:
                continue
            
            bufferLine = None
            bufferLineClipped = None
            mpl = []
            if clipBaselineBuffer.isMultipart():
                bufferMultiPolygon = clipBaselineBuffer.asMultiPolygon()
                size = len( bufferMultiPolygon )
                if size < 1:
                    continue
                for j in range( 0, size):
                    rings = len( bufferMultiPolygon[j] )
                    for k in range( 0, rings ):
                        mpl.append( bufferMultiPolygon[j][k] )
                bufferLine = QgsGeometry.fromMultiPolylineXY( mpl )
            else:
                bufferPolygon = clipBaselineBuffer.asPolygon()
                size = len( bufferPolygon )
                if size < 1:
                    continue
                
                for j in range( 0, size ):
                    mpl.append( bufferPolygon[j] )
                
                bufferLine = QgsGeometry.fromMultiPolylineXY( mpl )
            
            bufferLineClipped = bufferLine.intersection( stratumGeom )
            
            if bufferLineClipped and bufferLineClipped.type() == QgsWkbTypes.LineGeometry:
                #if stratumGeom is a multipolygon, bufferLineClipped must intersect each part
                bufferLineClippedIntersectsStratum = True
                if QgsWkbTypes.flatType( stratumGeom.wkbType() ) == QgsWkbTypes.MultiPolygon:
                    multiPoly = stratumGeom.asMultiPolygon()
                    for x in range( 0, len( multiPoly ) ):
                        poly = QgsGeometry.fromPolygonXY( multiPoly[x] )
                        if not poly.intersects( bufferLineClipped ):
                            bufferLineClippedIntersectsStratum = False
                            break
                
                if bufferLineClippedIntersectsStratum:
                    return bufferLineClipped
            
            currentBufferDist /= 2.0
        
        return None #No solution found even with reduced tolerance
                
    def findBaselineGeometry( self, stratumId ):
        if self.baselineLayer is None:
            return None
        
        fReq = QgsFeatureRequest()
        fReq.setSubsetOfAttributes( [self.baselineStratumId], self.baselineLayer.fields() )
        baselineFeatures = self.baselineLayer.getFeatures( fReq )
        for f in baselineFeatures:
            if self.shareBaseline or ( stratumId == f.attribute( self.baselineStratumId ) ):
                return f.geometry()
            
        return None
    
    def bufferDistance( self, minDistanceFromAttribute ):
        bufferDist = minDistanceFromAttribute
        if self.baselineBufferDistance >= 0:
            bufferDist = self.baselineBufferDistance
        if self.minDistUnits == TransectDistanceUnits.Meters and self.stratumLayer.crs().mapUnits() == QgsUnitTypes.DistanceDegrees:
            bufferDist /= 111319.9
        return bufferDist
    
    def otherTransectWithinDistance( self, geom, minDistLayerUnit, minDistance, sIndex, lineFeatureMap, distanceArea ):
        
        geomBuffer = geom.buffer( minDistLayerUnit, 8 )
        if geomBuffer is None:
            return False
        
        rect = geomBuffer.boundingBox()
        lineIdList = sIndex.intersects( rect )
        for lineId in lineIdList:
            idGeom = lineFeatureMap.get( lineId )
            if idGeom:
                dist = 0.0
                #closestSegmentPoint( geom1, geom2 ) -> dist, p1, p2
                closestSegmentResult = self.closestSegmentPoint( geom, idGeom )
                if closestSegmentResult[0] is None:
                    continue
                p1 = closestSegmentResult[2]
                p2 = closestSegmentResult[3]
                dist = distanceArea.measureLine( p1, p2 )
                if dist < minDistance:
                    return True
                
        return False
        
    def closestSegmentPoint( self, geom1, geom2 ):
        falseReturn =  [ False, 0, QgsPointXY( 0, 0 ), QgsPointXY( 0, 0 )]
    
        if geom1 is None or QgsWkbTypes.flatType( geom1.wkbType() ) != QgsWkbTypes.LineString:
            return falseReturn
        
        if geom2 is None or QgsWkbTypes.flatType( geom2.wkbType() ) != QgsWkbTypes.LineString:
            return falseReturn
        
        pl1 = geom1.asPolyline()
        pl2 = geom2.asPolyline()
        
        if len( pl1 ) < 2 or len( pl2 ) < 2:
            return falseReturn
        
        p11 = pl1[0]
        p12 = pl1[1]
        p21 = pl2[0]
        p22 = pl2[1]
        
        p1x = p11.x()
        p1y = p11.y()
        v1x = p12.x() - p11.x()
        v1y = p12.y() - p11.y()
        p2x = p21.x()
        p2y = p21.y()
        v2x = p22.x() - p21.x()
        v2y = p22.y() - p21.y()
        
        denominatorU = v2x * v1y - v2y * v1x;
        denominatorT = v1x * v2y - v1y * v2x
        
        if qgsDoubleNear( denominatorU, 0 ) or qgsDoubleNear( denominatorT, 0 ):
            minDistResult1 = p11.sqrDistToSegment( p21.x(), p21.y(), p22.x(), p22.y() )
            d1 = minDistResult1[0]
            minDistPoint1 = minDistResult1[1]
            minDistResult2 = p12.sqrDistToSegment( p21.x(), p21.y(), p22.x(), p22.y() )
            d2 = minDistResult2[0]
            minDistPoint2 = minDistResult2[1]
            minDistResult3 = p21.sqrDistToSegment( p11.x(), p11.y(), p12.x(), p12.y() )
            d3 = minDistResult3[0]
            minDistPoint3 = minDistResult3[1]
            minDistResult4 = p22.sqrDistToSegment( p11.x(), p11.y(), p12.x(), p12.y() )
            d4 = minDistResult4[0]
            minDistPoint4 = minDistResult4[1]
            
            if d1 <= d2 and d1 <= d3 and d1 <= d4:
                dist = math.sqrt( d1 )
                return [ True, dist, p11, minDistPoint1 ]
            
            elif d2 <= d1 and d2 <= d3 and d2 <= d4:
                dist = math.sqrt( d2 )
                return [ True, dist, p12, minDistPoint2 ]
            
            elif d3 <= d1 and d3 <= d2 and d3 <= d4:
                dist = math.sqrt( d3 )
                return [ True, dist, p21, minDistPoint3 ]
            
            else:
                dist = math.sqrt( d4 )
                return [ True, dist, p22, minDistPoint4 ]
            
        u = ( p1x * v1y - p1y * v1x - p2x * v1y + p2y * v1x ) / denominatorU
        t = ( p2x * v2y - p2y * v2x - p1x * v2y + p1y * v2x ) / denominatorT
        
        pt1 = QgsPointXY()
        pt2 = QgsPointXY()
        
        if u >= 0.0 and u <= 1.0 and t>= 0.0 and t <= 1.0:
            dist = 0
            pt1.setX( p2x + u * v2x )
            pt1.setY( p2y + u * v2y )
            pt2 = pt1
            dist = 0
            return [ True, dist, pt1, pt2 ]
        
        if t > 1.0:
            pt1.setX( p12.x() )
            pt1.setY( p12.y() )
        elif t < 0.0:
            pt1.setX( p11.x() )
            pt1.setY( p11.y() )
        if u > 1.0:
            pt2.setX( p22.x() )
            pt2.setY( p22.y() )
        elif u < 0.0:
            pt2.setX( p21.x() )
            pt2.setY( p21.y() )
        if t >= 0.0 and t <= 1.0:
            pt1 = pt2.sqrDistToSegment( p11.x(), p11.y(), p12.x(), p12.y() )[1]
        if u >= 0.0 and u <= 1.0:
            pt2 = pt1.sqrDistToSegment( p21.x(), p21.y(), p22.x(), p22.y() )[1]
            
        dist = math.sqrt( pt1.sqrDist( pt2 ) )
        return [ True, dist, pt1, pt2 ]
    
    def closestMultilineElement( self, pt, multiLine ):
        if multiLine is None or QgsWkbTypes.flatType( multiLine.wkbType() ) != QgsWkbTypes.MultiLineString:
            return None
        
        minDist = sys.float_info.max
        currentDist = 0.0
        currentLine = None
        closestLine = None
        
        for i in range( 0, multiLine.numGeometries() ):
            currentLine = multiLine.geometryN( i )
            currentDist = pt.distance( currentLine )
            if currentDist < minDist:
                minDist = currentDist
                closestLine = currentLine
                
        return closestLine
        
        
