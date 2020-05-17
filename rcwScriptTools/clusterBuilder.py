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


class clusterBuffer(QgsProcessingAlgorithm):


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return clusterBuffer()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'clusterbuffer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Setup 02: Cluster Creation')

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
        return self.tr("Creates cavity tree clusters.")

    def initAlgorithm(self, config=None):
        priWorkDir = os.path.join(os.path.dirname(__file__), '../output/')
        self.addParameter(QgsProcessingParameterVectorLayer('cavitytreelocations', 'Cavity Tree', types=[QgsProcessing.TypeVectorPoint], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('acresAdded', 'Acres', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='Acres.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Clusterbuffer', 'Cluster Buffer - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='concave_buffer.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Isobuffer', 'isoBuffer - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='isoBuffer.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('ConvexHull', 'Convex Hull - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='convex_hull.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Newcluster', 'new Cluster - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='newCluster.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Smallclusters', 'small Clusters - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='small_clusters.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Assigned', 'Assigned - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=False, defaultValue='Assigned.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Unassigned', 'Unassigned - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='Unassigned.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Isotrees', 'isoTrees - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='isoTrees.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Clusterfinal', 'cluster Final - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='clusterFinal.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Fielddrop', 'fieldDrop - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='fieldDrop.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('ConcaveHull', 'Concave Hull - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='concave_hull.shp'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(11, model_feedback)
        results = {}
        outputs = {}

        # Isolate and Build Clusters
        alg_params = {
            'FIELD': 'Cluster_ID',
            'INPUT': parameters['cavitytreelocations'],
            'OPERATOR': 0,
            'VALUE': '2500',
            'FAIL_OUTPUT': parameters['Assigned'],
            'OUTPUT': parameters['Unassigned']
        }
        outputs['IsolateAndBuildClusters'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Assigned'] = outputs['IsolateAndBuildClusters']['FAIL_OUTPUT']
        results['Unassigned'] = outputs['IsolateAndBuildClusters']['OUTPUT']

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Build Clusters
        alg_params = {
            'FIELD': 'Cluster_ID',
            'INPUT': outputs['IsolateAndBuildClusters']['FAIL_OUTPUT'],
            'KNEIGHBORS': 3,
            'OUTPUT': parameters['ConcaveHull']
        }
        outputs['BuildClusters'] = processing.run('qgis:knearestconcavehull', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['ConcaveHull'] = outputs['BuildClusters']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # 200ft Cluster Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 61,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['BuildClusters']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': parameters['Clusterbuffer']
        }
        outputs['FtClusterBuffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Clusterbuffer'] = outputs['FtClusterBuffer']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Convex hull
        alg_params = {
            'INPUT': outputs['FtClusterBuffer']['OUTPUT'],
            'OUTPUT': parameters['ConvexHull']
        }
        outputs['ConvexHull'] = processing.run('native:convexhull', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['ConvexHull'] = outputs['ConvexHull']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Less than three
        alg_params = {
            'INPUT': outputs['IsolateAndBuildClusters']['FAIL_OUTPUT'],
            'INTERSECT': outputs['ConvexHull']['OUTPUT'],
            'PREDICATE': [2],
            'OUTPUT': parameters['Isotrees']
        }
        outputs['LessThanThree'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Isotrees'] = outputs['LessThanThree']['OUTPUT']

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Combine by Cluster ID
        alg_params = {
            'FIELD': 'Cluster_ID',
            'INPUT': outputs['LessThanThree']['OUTPUT'],
            'OUTPUT': parameters['Smallclusters']
        }
        outputs['CombineByClusterId'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Smallclusters'] = outputs['CombineByClusterId']['OUTPUT']

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Buffer - iso
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 114,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['CombineByClusterId']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': parameters['Isobuffer']
        }
        outputs['BufferIso'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Isobuffer'] = outputs['BufferIso']['OUTPUT']

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # New - Convex hull
        alg_params = {
            'INPUT': outputs['BufferIso']['OUTPUT'],
            'OUTPUT': parameters['Newcluster']
        }
        outputs['NewConvexHull'] = processing.run('native:convexhull', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Newcluster'] = outputs['NewConvexHull']['OUTPUT']

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Combine Clusters
        alg_params = {
            'CRS': None,
            'LAYERS': [outputs['ConvexHull']['OUTPUT'],outputs['NewConvexHull']['OUTPUT']],
            'OUTPUT': parameters['Clusterfinal']
        }
        outputs['CombineClusters'] = processing.run('native:mergevectorlayers', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Clusterfinal'] = outputs['CombineClusters']['OUTPUT']

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Drop field(s)
        alg_params = {
            'COLUMN': 'TREENO;TRAINING_I;STRBAND;SPECIES;SPECIES50;SPECIES200;NORTHING;EASTING;INSTLN_ID;HEIGHT50;HEIGHT200;FLAT_TOP;DIAMETER;DENSITY50;DENSITY200;COMMENTS;OBJECTID;id;layer;path;regcode;rcuid;training',
            'INPUT': outputs['CombineClusters']['OUTPUT'],
            'OUTPUT': parameters['Fielddrop']
        }
        outputs['DropFields'] = processing.run('qgis:deletecolumn', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Fielddrop'] = outputs['DropFields']['OUTPUT']

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Add Acres Feild
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'acres',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'value = $geom.area() * 0.000247105',
            'GLOBAL': '',
            'INPUT': outputs['DropFields']['OUTPUT'],
            'OUTPUT': parameters['acresAdded']
        }
        outputs['AddAcresFeild'] = processing.run('qgis:advancedpythonfieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['acresAdded'] = outputs['AddAcresFeild']['OUTPUT']
        return results

"""
    def name(self):
        return 'clusterbuffer'

    def displayName(self):
        return 'Cluster Buffer'

    def group(self):
        return 'HMDB'

    def groupId(self):
        return 'HMDB'

    def createInstance(self):
        return ClusterBuffer()
"""