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
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingParameterFeatureSink
import os


class cavityTreeBuffer(QgsProcessingAlgorithm):


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return cavityTreeBuffer()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'cavitytreebuffer'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Setup 01: Cavity Tree and 200ft Buffer Creation')

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
        return self.tr("Creates cavity tree point file and generates a 200ft voronoi buffer.")


    def initAlgorithm(self, config=None):
        scriptPath = os.path.dirname(os.path.abspath(__file__))
        outputDir = os.path.join(scriptPath, '../output/')
        styleDir = os.path.join(scriptPath, '../data/styles/')
        self.addParameter(QgsProcessingParameterVectorLayer('tbl_trees', 'Tree Table', types=[QgsProcessing.TypeFile], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('cavitytreelocations', 'Cavity Tree Locations', type=QgsProcessing.TypeVectorPoint, createByDefault=True, defaultValue='cavityTree.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Tree_voronoi_clip', 'Tree 200ft Voronoi', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='tree_voronoi_clip.shp'))
        self.addParameter(QgsProcessingParameterVectorDestination('Tree_voronoi', 'Tree Voronoi - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='tree_voronoi.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('TreeBuffer', 'Tree Buffer - Uncheck', type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue='tree_buffer.shp'))
        self.addParameter(QgsProcessingParameterFeatureSink('Tree_disolve', 'Tree Disolve - Uncheck', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='tree_disolve.shp'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        crs = QgsCoordinateReferenceSystem('EPSG:32617')
        results = {}
        outputs = {}


        # Create cavity tree Point file from table
        alg_params = {
            'INPUT' : parameters['tbl_trees'],
            #'INPUT' : 'dbname=\'postgis_SDE\' host=152.46.16.212 port=5432 sslmode=disable authcfg=j90qj62 key=\'objectid,treeno\' checkPrimaryKeyUnicity=\'1\' table=\"rcw\".\"tbl_trees\" sql='',
            'XFIELD' : 'easting',
            'YFIELD' : 'northing',
            'TARGET_CRS' : 'EPSG:32617',
            'MFIELD' : None,
            'ZFIELD' : None,
            'OUTPUT' : parameters['cavitytreelocations']
        }
        outputs['CavityTree'] = processing.run('qgis:createpointslayerfromtable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['cavityTreeLocations'] = outputs['CavityTree']['OUTPUT']

        """
        # Collects user input var
        ESPG = self.parameterAsDouble(
            parameters,
            'ESPG',
            context
        )
        """

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # v.voronoi
        alg_params = {
            '-l': False,
            '-t': False,
            'GRASS_MIN_AREA_PARAMETER': 0.0001,
            'GRASS_OUTPUT_TYPE_PARAMETER': 0,
            'GRASS_REGION_PARAMETER': None,
            'GRASS_SNAP_TOLERANCE_PARAMETER': -1,
            'GRASS_VECTOR_DSCO': '',
            'GRASS_VECTOR_EXPORT_NOCAT': False,
            'GRASS_VECTOR_LCO': '',
            'input': outputs['CavityTree']['OUTPUT'],
            'output': parameters['Tree_voronoi']
        }
        outputs['Vvoronoi'] = processing.run('grass7:v.voronoi', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Tree_voronoi'] = outputs['Vvoronoi']['output']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Buffer -tree
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 61,
            'END_CAP_STYLE': 0,
            'INPUT': outputs['CavityTree']['OUTPUT'],
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'SEGMENTS': 30,
            'OUTPUT': parameters['TreeBuffer']
        }
        outputs['BufferTree'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['TreeBuffer'] = outputs['BufferTree']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Dissolve
        alg_params = {
            'FIELD': '[all]',
            'INPUT': outputs['BufferTree']['OUTPUT'],
            'OUTPUT': parameters['Tree_disolve']
        }
        outputs['Dissolve'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Tree_disolve'] = outputs['Dissolve']['OUTPUT']

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Clip
        alg_params = {
            'INPUT': outputs['Vvoronoi']['output'],
            'OVERLAY': outputs['Dissolve']['OUTPUT'],
            'OUTPUT': parameters['Tree_voronoi_clip']
        }
        outputs['Clip'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Tree_voronoi_clip'] = outputs['Clip']['OUTPUT']
        return results

    """
    def name(self):
        return 'cavityTreeBuffer'

    def displayName(self):
        return 'cavityTreeBuffer'

    def group(self):
        return 'HMDB'

    def groupId(self):
        return 'HMDB'

    def createInstance(self):
        return cavityTreeBuffer()
    """