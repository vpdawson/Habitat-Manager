
"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
# Import standard modules
import os
import sys
import csv
import datetime
import re

# Import XML modules
#import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, Comment, tostring, XML, ElementTree
from xml.dom import minidom
#from ElementTree_pretty import prettify - not needed

# Import QGIS modules
from qgis import processing
from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import QgsProcessingUtils
from qgis.core import QgsProcessing
from qgis.core import QgsProject
from qgis.core import QgsFeatureRequest
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFeatureSource


class impactAssessment(QgsProcessingAlgorithm):

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return impactAssessment()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'impactAssessment'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Task: Impact Assessment')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Habitat Management scripts')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'habitatmanagementscripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Identifies cavity tree, stands and partitions potentially impacted by proposed new construction, then re-evaluates foraging habitat suitability and applies new 'stand' and 'partition' score values to impacted stand anad partition vector files.")


    def initAlgorithm(self, config=None):
        projectPath = os.path.join(QgsProject.instance().homePath())
        scriptPath = os.path.dirname(os.path.abspath(__file__))
        outputDir = os.path.join(scriptPath, '../output/')
        styleDir = os.path.join(scriptPath, '../data/styles/')
        style1 = styleDir + "/ImpactTreeMarkUp.qml" # cavityTree_impact.loadNamedStyle(style1), 
        style2 = styleDir + "/clusterImpactMarkUp.qml" # cluster_impact.loadNamedStyle(style2),
        style3 = styleDir + "/qrtImpactMarkUp.qml" # 1_4M_impact.loadNamedStyle(style3),
        style4 = styleDir + "/halfImpactMarkUp.qml" # 1_2M_impact.loadNamedStyle(style4),
        style5 = styleDir + "/standImpactMarkUp.qml" # stand_impact.loadNamedStyle(style5),
        standardDir = os.path.join(scriptPath, '../data/standards/')
        self.addParameter(QgsProcessingParameterVectorLayer('cavitytree', 'Cavity Trees', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('clusters', 'Custer 10 Acres Plus', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('14mpartition', '1/4Mile Partition', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('12mpartition', '1/2Mile Partition', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('foreststand', 'Stand Prep', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('impactfeature', 'Impact Feature', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('cavityTreeImpact', 'Cavity Tree Impact', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='cavityTree_impact.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('clusterImpact', 'Cluster Impact', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='cluster_impact.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('14mImpact', '1/4Mile Impact', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='qtrImpact.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('12mImpact', '1/2Mile Impact', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='halfImpact.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('standImpact', 'Stand Impact', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='stand_impact.shp'))

    def processAlgorithm(self, parameters, context, model_feedback):
        """
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )
        """


        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}

        # Extract by location
        alg_params = {
            'INPUT': parameters['cavitytree'],
            'INTERSECT': parameters['impactfeature'],
            'PREDICATE': [0,4,5,6],
            'OUTPUT': parameters['cavityTreeImpact']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['cavityTreeImpact'] = outputs['ExtractByLocation']['OUTPUT']
        
        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}
            
            
        # Extract by location
        alg_params = {
            'INPUT': parameters['clusters'],
            'INTERSECT': parameters['impactfeature'],
            'PREDICATE': [4,5,6],
            'OUTPUT': parameters['clusterImpact']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['clusterImpact'] = outputs['ExtractByLocation']['OUTPUT']
        
        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
            
        # Extract by location
        alg_params = {
            'INPUT': parameters['14mpartition'],
            'INTERSECT': parameters['impactfeature'],
            'PREDICATE': [0,4,5,6],
            'OUTPUT': parameters['14mImpact']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['14mImpact'] = outputs['ExtractByLocation']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}
            
        # Extract by location
        alg_params = {
            'INPUT': parameters['12mpartition'],
            'INTERSECT': parameters['impactfeature'],
            'PREDICATE': [0,4,6,7],
            'OUTPUT': parameters['12mImpact']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['12mImpact'] = outputs['ExtractByLocation']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}
            
            
        # Extract by location
        alg_params = {
            'INPUT': parameters['foreststand'],
            'INTERSECT': parameters['impactfeature'],
            'PREDICATE': [0,1,4,5],
            'OUTPUT': parameters['standImpact']
        }
        outputs['ExtractByLocation'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['standImpact'] = outputs['ExtractByLocation']['OUTPUT']


        return results        
        #print(outputs)    


        #_____________________________________________________________
        # to get hold of the layer in post processing
        #self.dest_id = dest_id
        #self.result_type = result_type

        #return {'OUTPUT': dest_id}
        
        #--------------------------------------------------------------
        #cavityTree_impact.loadNamedStyle(style1), 
        #cluster_impact.loadNamedStyle(style2)
        #qtrImpact.loadNamedStyle(style3)
        #halfImpact.loadNamedStyle(style4),
        #stand_impact.loadNamedStyle(style5),

        
    """
    def postProcessAlgorithm(self, context, model_feedback):
        '''
        PostProcessing to define the Symbology
        '''
        styles = []
        # error - AttributeError: 'NoneType' object has no attribute 'loadNamedStyle'
        styles['standImpact']= QgsProcessingUtils.mapLayerFromString('standImpact', context).loadNamedStyle(style5)
        #QgsProcessingUtils.mapLayerFromString(self.dest_id, context).loadNamedStyle(style_path)
        #QgsProcessingUtils.mapLayerFromString(self.dest_id, context).loadNamedStyle(style_path)
        
        
        
        #output = QgsProcessingUtils.mapLayerFromString(self.dest_id, context)
        #path = ='./path/to/style.qml'
        #if output == parameters['standImpact']:
        #output.loadNamedStyle(style5)
        #output.triggerRepaint()
        return styles
    

    def postProcessAlgorithm(self, context, model_feedback):
        retval = super().postProcessAlgorithm(context, feedback)
        if self.result_type == 'UNION':
            style_file = 'style_union.qml'
        elif self.result_type == 'INTERSECTION':
            style_file = 'style_intersection.qml'
        else:
            style_file = 'style.qml'
        style_path = os.path.join(os.path.dirname(__file__), 'resources', style_file)
        QgsProcessingUtils.mapLayerFromString(self.dest_id, context).loadNamedStyle(style_path)
        return retval



    
    """