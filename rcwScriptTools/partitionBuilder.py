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


class partitionBuffer(QgsProcessingAlgorithm):


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return partitionBuffer()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'partitionbuffer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Setup 04: Cluster Center and Partition Buffer Creation')

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
        return self.tr("Determines cluster centers, and generates 1/4 and 1/2 Mile voronoi buffers.")



    def initAlgorithm(self, config=None):
        priWorkDir = os.path.join(os.path.dirname(__file__), '../output/')
        self.addParameter(QgsProcessingParameterVectorLayer('cavitytreelocations', 'Cavity Tree', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Cluster_center', 'Cluster Centers', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue='cluster_center.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_4m_voronoi', '1/4M voronoi', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='1_4M_voronoi.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_2m_voronoi', '1/2M voronoi', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='1_2M_voronoi.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_4m_cluster_buffer', '1/4M buffer - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='1_4M_cluster_buffer.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_2m_cluster_buffer', '1/2M buffer - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='1_2M_cluster_buffer.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_4m_disolve', '1/4M disolve - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='1_4M_disolve.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('1_2m_disolve', '1/2M disolve - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='1_2M_disolve.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('VoronoiCenters', 'Voronoi Centers - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='voronoi_center.shp'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(8, model_feedback)
        results = {}
        outputs = {}

        # Cavity Tree Cluster Centers
        alg_params = {
            'INPUT': parameters['cavitytreelocations'],
            'UID': 'Cluster_ID',
            'WEIGHT': None,
            'OUTPUT': parameters['Cluster_center']
        }
        outputs['CavityTreeClusterCenters'] = processing.run('native:meancoordinates', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Cluster_center'] = outputs['CavityTreeClusterCenters']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Buffer-12
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 804.672,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['CavityTreeClusterCenters']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': parameters['1_2m_cluster_buffer']
        }
        outputs['Buffer12'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_2m_cluster_buffer'] = outputs['Buffer12']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Cluster Center Voronoi
        alg_params = {
            'BUFFER': 100,
            'INPUT': outputs['CavityTreeClusterCenters']['OUTPUT'],
            'OUTPUT': parameters['VoronoiCenters']
        }
        outputs['ClusterCenterVoronoi'] = processing.run('qgis:voronoipolygons', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['VoronoiCenters'] = outputs['ClusterCenterVoronoi']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Buffer-14
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 402.336,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['CavityTreeClusterCenters']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': parameters['1_4m_cluster_buffer']
        }
        outputs['Buffer14'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_4m_cluster_buffer'] = outputs['Buffer14']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Dissolve-14
        alg_params = {
            'FIELD': 'all',
            'INPUT': outputs['Buffer14']['OUTPUT'],
            'OUTPUT': parameters['1_4m_disolve']
        }
        outputs['Dissolve14'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_4m_disolve'] = outputs['Dissolve14']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Dissolve-12
        alg_params = {
            'FIELD': 'all',
            'INPUT': outputs['Buffer12']['OUTPUT'],
            'OUTPUT': parameters['1_2m_disolve']
        }
        outputs['Dissolve12'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_2m_disolve'] = outputs['Dissolve12']['OUTPUT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Clip-14
        alg_params = {
            'INPUT': outputs['ClusterCenterVoronoi']['OUTPUT'],
            'OVERLAY': outputs['Dissolve14']['OUTPUT'],
            'OUTPUT': parameters['1_4m_voronoi']
        }
        outputs['Clip14'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_4m_voronoi'] = outputs['Clip14']['OUTPUT']

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Clip-12
        alg_params = {
            'INPUT': outputs['ClusterCenterVoronoi']['OUTPUT'],
            'OVERLAY': outputs['Dissolve12']['OUTPUT'],
            'OUTPUT': parameters['1_2m_voronoi']
        }
        outputs['Clip12'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['1_2m_voronoi'] = outputs['Clip12']['OUTPUT']
        return results

    """
    def name(self):
        return 'partitionBuffer'

    def displayName(self):
        return 'partitionBuffer'

    def group(self):
        return 'HMDB'

    def groupId(self):
        return 'HMDB'

    def createInstance(self):
        return Partitionbuffer()
    """
