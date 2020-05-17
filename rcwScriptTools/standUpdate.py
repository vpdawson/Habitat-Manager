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
from qgis.core import QgsProject
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsFeatureRequest
import os
from qgis.utils import iface


class standUpdate(QgsProcessingAlgorithm):

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return standUpdate()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'standupdate'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Setup 05: Stand File Preperation')

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
        return self.tr("Adds fields required for task evaluations \nCan be skipped if stand layer is current.")
                        # 'Does one some combination of the following tasks: \nApplies or updates stand table data to stand layer \n Adds fields required for task evaluations \nCan be skipped if stand layer is current.'
    def initAlgorithm(self, config=None):
        priWorkDir = os.path.join(os.path.dirname(__file__), '../output/')
        self.addParameter(QgsProcessingParameterVectorLayer('standdata', 'Raw Forest Stand', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Standprep', 'standPrep', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue='standPrep.shp'))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(32, model_feedback)
        results = {}
        outputs = {}

        #----------------------------------------------------------------
        #   Stand Recovery Grading Fields
        #----------------------------------------------------------------
        # Add Grade Feild for Pine TPA 14+"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rNum14',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': parameters['standdata'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rNum14'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine BA 14+"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rPBA14',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rNum14']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rpba14'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        #results['standTemp'] = outputs['spba14']['OUTPUT']

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine BA 10-13.9"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rPBA10',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rpba14']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rpba10'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine BA 4-9.9"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rPBA4',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rpba10']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rpba4'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine TPA 4-9.9"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rNum4',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rpba4']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rNum4'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine BA => 10in (Per/Acre)
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rPBAall',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rNum4']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rpbaall'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for % Herbaceous Groundcover
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rHerbGnd',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rpbaall']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rherbgnd'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for HWD Midstory
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rHWDMID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rherbgnd']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rhwdmid'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for % HW Canopy Combined LL & OP
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rPerHwCan',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rhwdmid']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rPerHwCan'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine Age
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rPineAge',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rPerHwCan']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rpineage'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Fire Return Interval
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rFRI',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rpineage']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rfri'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Season of Prescribed Burn
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rSoPB',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rfri']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rsopb'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(13)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Sum of Weighted Scores
        alg_params = {
            'FIELD_LENGTH': 4,
            'FIELD_NAME': 'rSumWS',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 1, # 0=int, 1=float, 2=str
            'INPUT': outputs['rsopb']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rsumws'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(14)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for GQFH Indicator (suitable=1, non=0)
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'gqfhI',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rsumws']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['gqfhi'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(15)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Acres GQFH
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'gqfhA',
            'FIELD_PRECISION': 2,
            'FIELD_TYPE': 1, # 0=int, 1=float, 2=str
            'INPUT': outputs['gqfhi']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['gqfha'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(16)
        if feedback.isCanceled():
            return {}

        #----------------------------------------------------------------
        #   Partition Recovery Grading Fields
        #----------------------------------------------------------------

        # Add Grade Feild for total acres of GQFH in partition
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rgqfhA_P',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['gqfha']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rgqfha_p'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(17)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for total acres of pine in the partition
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rtaPinePar',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rgqfha_p']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rtapinepar'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(18)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for total acres of GQFH within 1/4 mile
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rtaPineQt',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rtapinepar']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rtapineqt'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(19)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for # of contiguous foraging acres
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'rCFA',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rtapineqt']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rcfa'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(20)
        if feedback.isCanceled():
            return {}

        # Add Feild for recovery standard recommendations
        alg_params = {
            'FIELD_LENGTH': 50,
            'FIELD_NAME': 'rRecmnd',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2, # 0=int, 1=float, 2=str
            'INPUT': outputs['rcfa']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['rRecmnd'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        #----------------------------------------------------------------
        #   Stand Managed Stability Grading Fields
        #----------------------------------------------------------------
        # Add Grade Feild for Pine Age
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msPineAge',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['rRecmnd']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mspineage'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(21)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine BA => 10in (Per/Acre)
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msPBAall',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mspineage']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mspbaall'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(22)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Pine BA 4-9.9"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msPBA4',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mspbaall']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mspba4'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(23)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for HWD Midstory
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msHWDMID',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mspba4']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mshwdmid'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(24)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Total Basal Area including Hardwood graded vs. area?


        '''-------------------INSERT 2nd TBA FIELD IF NEEDED-------------------------'''


        # Add Grade Feild for Total Basal Area including Hardwood - grade?
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'mstba_hwd',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mshwdmid']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mstba_hwd'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for % Herbaceous Groundcover
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msHerbGnd',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mstba_hwd']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['msherbgnd'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(25)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Fire Return Interval
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msFRI',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['msherbgnd']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['msfri'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(26)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Season of Prescribed Burn
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msSoPB',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['msfri']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mssopb'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(27)
        if feedback.isCanceled():
            return {}

        #----------------------------------------------------------------
        #   Partition Managed Stability Grading Fields
        #----------------------------------------------------------------

        # Add Grade Feild for total acres of GQFH in partition
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msgqfhAP',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mssopb']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['msgqfhap'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(28)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for total acres of GQFH within 1/4 mile
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'mstaPineQt',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['msgqfhap']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mstapineqt'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(29)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for total Basal Area (ft2) of pine >= 10" dbh
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msTBA10',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mstapineqt']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mstba10'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(30)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for # of contiguous foraging acres
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'msCFA',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['mstba10']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['mscfa'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        # Add Feild for MS standard recommendations
        alg_params = {
            'FIELD_LENGTH': 50,
            'FIELD_NAME': 'msRecmnd',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 2, # 0=int, 1=float, 2=str
            'INPUT': outputs['mscfa']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['msRecmnd'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(31)
        if feedback.isCanceled():
            return {}

        #----------------------------------------------------------------
        #   More common use fields
        #----------------------------------------------------------------

        # Add Grade Feild for % HW Canopy Long Leaf Pine
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'phwcLLP',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['msRecmnd']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['phwcllp'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for % HW Canopy Other Pine
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'phwcOP',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['phwcllp']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['phwcop'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Total PBA value over 10"
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'pbaOver10',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['phwcop']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['pbaOver10'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        #----------------------------------------------------------------
        #   Overall Scores
        #----------------------------------------------------------------

        # Add Grade Feild for GQFH
        alg_params = {
            'FIELD_LENGTH': 3,
            'FIELD_NAME': 'GQFH',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 1, # 0=int, 1=float, 2=str
            'INPUT': outputs['mscfa']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['gqfh'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(32)
        if feedback.isCanceled():
            return {}

        # Add Grade Feild for Habitat Suitability
        alg_params = {
            'FIELD_LENGTH': 2,
            'FIELD_NAME': 'habSuit',
            'FIELD_PRECISION': 0,
            'FIELD_TYPE': 0, # 0=int, 1=float, 2=str
            'INPUT': outputs['gqfh']['OUTPUT'],
            'OUTPUT': parameters['Standprep']
        }
        outputs['Gqfh'] = processing.run('qgis:addfieldtoattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Standprep'] = outputs['Gqfh']['OUTPUT']
        return results
