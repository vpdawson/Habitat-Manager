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
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import os


class partitionBuilder(QgsProcessingAlgorithm):

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return partitionBuilder()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'partitionbuilder'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Setup 06: Creates gradeable Partitions')

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
        return self.tr("Incorporates stand layer data to 1/4 and 1/2 Mile partitions.")

    def initAlgorithm(self, config=None):
        priWorkDir = os.path.join(os.path.dirname(__file__), '../output/')
        self.addParameter(QgsProcessingParameterVectorLayer('14mvoronoi', '1/4M voronoi', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('12mvoronoi2', '1/2M voronoi', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterVectorLayer('foreststands', 'Stand Prep', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('1_4m_partiton', '1/4M Partiton', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='1_4M_partition.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_2m_partition', '1/2M Partition', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='1_2M_partition.shp'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(2, model_feedback)
        results = {}
        outputs = {}

        # Intersection - 14
        alg_params = {
            'INPUT': parameters['14mvoronoi'],
            'INPUT_FIELDS': None,
            'OVERLAY': parameters['foreststands'],
            'OVERLAY_FIELDS': None,
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': parameters['1_4m_partiton']
        }
        outputs['Intersection14'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_4m_partiton'] = outputs['Intersection14']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Intersection - 12
        alg_params = {
            'INPUT': parameters['12mvoronoi2'],
            'INPUT_FIELDS': None,
            'OVERLAY': parameters['foreststands'],
            'OVERLAY_FIELDS': None,
            'OVERLAY_FIELDS_PREFIX': '',
            'OUTPUT': parameters['1_2m_partition']
        }
        outputs['Intersection12'] = processing.run('native:intersection', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_2m_partition'] = outputs['Intersection12']['OUTPUT']
        return results

