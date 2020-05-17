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
from qgis import processing
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import QgsProject
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsFeatureRequest
import os
from qgis.utils import iface


class clusterCheck(QgsProcessingAlgorithm):


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return clusterCheck()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'clustercheck'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Setup 03: Cluster Check')

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
        return self.tr("Checks cluster acrage and adjusts if size is less than 10 acres, untill a minimum of 10 acres is met.")

    def initAlgorithm(self, config=None):
        priWorkDir = os.path.join(os.path.dirname(__file__), '../output/')
        self.addParameter(QgsProcessingParameterVectorLayer('acresadded', 'Acres', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Cluster10plus', 'Cluster 10 Plus Acres', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='cluster10Plus.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Update1', 'First Update - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress.
        feedback = QgsProcessingMultiStepFeedback(10, model_feedback)
        results = {}
        outputs = {}

        """
        # loops through acres column
        layer = iface.activeLayer() # layer must be selected in console - need better solution
        #layer = parameters['acresAdded']
        clusters = layer.getFeatures()
        for cluster in clusters:
            field = cluster.attributes()
            acres = field[3]
            #print (acres)
            if acres <10:
                print (acres)
                #acres.bufferDraw= True
                #acres.bufferColor= QColor("red")
                #acres.bufferSize = 100

        """


        # 1st Extract
        alg_params = {
            'FIELD': 'acres',
            'INPUT': parameters['acresadded'],
            'OPERATOR': 4,
            'VALUE': '10',
            'FAIL_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StExtract'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # 1st Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 25,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['StExtract']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StBuffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # 1st reassess area
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': ' $area ',
            'INPUT': outputs['StBuffer']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StReassessArea'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # 1st reassess acres
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'acres',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': ' \"area\"  * 0.000247105',
            'INPUT': outputs['StReassessArea']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['StReassessAcres'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # 1st Merge
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['StReassessAcres']['OUTPUT'],outputs['StExtract']['FAIL_OUTPUT']],
            'OUTPUT': parameters['Update1']
        }
        outputs['StMerge'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Update1'] = outputs['StMerge']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # 2nd Extract
        alg_params = {
            'FIELD': 'acres',
            'INPUT': outputs['StMerge']['OUTPUT'],
            'OPERATOR': 4,
            'VALUE': '10',
            'FAIL_OUTPUT': QgsProcessing.TEMPORARY_OUTPUT,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NdExtract'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # 2nd Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 15,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['NdExtract']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NdBuffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # 2nd reassess area
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'area',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': ' $area ',
            'INPUT': outputs['NdBuffer']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NdReassessArea'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # 2nd reassess acres
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'acres',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': '\"area\" * 0.000247105',
            'INPUT': outputs['NdReassessArea']['OUTPUT'],
            'NEW_FIELD': False,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['NdReassessAcres'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # 2nd Merge
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['NdReassessAcres']['OUTPUT'],outputs['NdExtract']['FAIL_OUTPUT']],
            'OUTPUT': parameters['Cluster10plus']
        }
        outputs['NdMerge'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Cluster10plus'] = outputs['NdMerge']['OUTPUT']
        return results

