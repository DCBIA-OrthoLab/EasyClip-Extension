from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import os
import numpy
import pickle
import json

#
# Load Files
#

class EasyClip(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Easy Clip"
        parent.categories = ["Surface Models"]
        parent.dependencies = []
        parent.contributors = ["Julia Lopinto, (University Of Michigan)", "Jean-Baptiste Vimort, (University Of Michigan)"]
        parent.helpText = """
        This Module is used to clip one or different 3D Models according to a predetermined plane.
        Plane can be saved to be reused for other models.
        After clipping, the models are closed and can be saved as new 3D Models.

        This is an alpha version of the module.
        It can't be used for the moment.
        """
        
        parent.acknowledgementText = """
            This work was supported by the National
            Institutes of Dental and Craniofacial Research
            and Biomedical Imaging and Bioengineering of
            the National Institutes of Health under Award
            Number R01DE024450.
            """
        
        self.parent = parent

class EasyClipWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)
        print "-------Easy Clip Widget Setup---------"
        # GLOBALS:
        self.logic = EasyClipLogic(self)
        self.ignoredNodeNames = ('Red Volume Slice', 'Yellow Volume Slice', 'Green Volume Slice')
        self.colorSliceVolumes = dict()
        self.dictionnaryModel = dict()
        self.hardenModelIDdict = dict()
        self.landmarkDescriptionDict = dict()
        self.planeControlsDictionary = {}
        # Instantiate and connect widgets
        #
        # Interface
        #
        loader = qt.QUiLoader()
        moduleName = 'EasyClip'
        scriptedModulesPath = eval('slicer.modules.%s.path' % moduleName.lower())
        scriptedModulesPath = os.path.dirname(scriptedModulesPath)
        path = os.path.join(scriptedModulesPath, 'Resources', 'UI', '%s.ui' %moduleName)

        qfile = qt.QFile(path)
        qfile.open(qt.QFile.ReadOnly)
        widget = loader.load(qfile, self.parent)
        self.layout = self.parent.layout()
        self.widget = widget
        self.layout.addWidget(widget)
        ##--------------------------- Scene --------------------------#
        self.SceneCollapsibleButton = self.logic.get("SceneCollapsibleButton") # this atribute is usefull for Longitudinal quantification extension
        treeView = self.logic.get("treeView")
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.sceneModel().setHorizontalHeaderLabels(["Models"])
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode']
        treeView.header().setVisible(False)
        self.autoChangeLayout = self.logic.get("autoChangeLayout")
        self.computeBox = self.logic.get("computeBox")
        self.computeBox.connect('clicked()', self.onComputeBox)
        #--------------------------- Clipping Part --------------------------#
        # CLIPPING BUTTONS

        self.red_plane_box = self.logic.get("red_plane_box")
        self.radio_red_Neg = self.logic.get("radio_red_Neg")
        self.radio_red_Neg.setIcon(qt.QIcon(":/Icons/RedSpaceNegative.png"))
        self.radio_red_Pos = self.logic.get("radio_red_Pos")
        self.radio_red_Pos.setIcon(qt.QIcon(":/Icons/RedSpacePositive.png"))
        self.red_plane_box.connect('clicked(bool)', lambda: self.logic.onCheckBoxClicked('Red',
                                                                                         self.red_plane_box,
                                                                                         self.radio_red_Neg))
        self.red_plane_box.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeRed",
                                                                                  self.red_plane_box.isChecked(),
                                                                                  self.radio_red_Neg.isChecked(),
                                                                                  self.radio_red_Pos.isChecked()))
        self.radio_red_Neg.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeRed",
                                                                                  self.red_plane_box.isChecked(),
                                                                                  self.radio_red_Neg.isChecked(),
                                                                                  self.radio_red_Pos.isChecked()))
        self.radio_red_Pos.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeRed",
                                                                                  self.red_plane_box.isChecked(),
                                                                                  self.radio_red_Neg.isChecked(),
                                                                                  self.radio_red_Pos.isChecked()))
        self.yellow_plane_box = self.logic.get("yellow_plane_box")
        self.radio_yellow_Neg= self.logic.get("radio_yellow_Neg")
        self.radio_yellow_Neg.setIcon(qt.QIcon(":/Icons/YellowSpaceNegative.png"))
        self.radio_yellow_Pos = self.logic.get("radio_yellow_Pos")
        self.radio_yellow_Pos.setIcon(qt.QIcon(":/Icons/YellowSpacePositive.png"))
        self.yellow_plane_box.connect('clicked(bool)', lambda: self.logic.onCheckBoxClicked('Yellow',
                                                                                            self.yellow_plane_box,
                                                                                            self.radio_yellow_Neg))
        self.yellow_plane_box.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeYellow",
                                                                                  self.yellow_plane_box.isChecked(),
                                                                                  self.radio_yellow_Neg.isChecked(),
                                                                                  self.radio_yellow_Pos.isChecked()))
        self.radio_yellow_Neg.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeYellow",
                                                                                  self.yellow_plane_box.isChecked(),
                                                                                  self.radio_yellow_Neg.isChecked(),
                                                                                  self.radio_yellow_Pos.isChecked()))
        self.radio_yellow_Pos.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeYellow",
                                                                                  self.yellow_plane_box.isChecked(),
                                                                                  self.radio_yellow_Neg.isChecked(),
                                                                                  self.radio_yellow_Pos.isChecked()))
        self.green_plane_box = self.logic.get("green_plane_box")
        self.radio_green_Neg= self.logic.get("radio_green_Neg")
        self.radio_green_Neg.setIcon(qt.QIcon(":/Icons/GreenSpaceNegative.png"))
        self.radio_green_Pos = self.logic.get("radio_green_Pos")
        self.radio_green_Pos.setIcon(qt.QIcon(":/Icons/GreenSpacePositive.png"))
        self.green_plane_box.connect('clicked(bool)', lambda: self.logic.onCheckBoxClicked('Green',
                                                                                           self.green_plane_box,
                                                                                           self.radio_green_Neg))
        self.green_plane_box.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeGreen",
                                                                                  self.green_plane_box.isChecked(),
                                                                                  self.radio_green_Neg.isChecked(),
                                                                                  self.radio_green_Pos.isChecked()))
        self.radio_green_Neg.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeGreen",
                                                                                  self.green_plane_box.isChecked(),
                                                                                  self.radio_green_Neg.isChecked(),
                                                                                  self.radio_green_Pos.isChecked()))
        self.radio_green_Pos.connect('clicked(bool)', lambda: self.updateSliceState("vtkMRMLSliceNodeGreen",
                                                                                  self.green_plane_box.isChecked(),
                                                                                  self.radio_green_Neg.isChecked(),
                                                                                  self.radio_green_Pos.isChecked()))
        self.ClippingButton = self.logic.get("ClippingButton")
        self.ClippingButton.connect('clicked()', self.ClippingButtonClicked)
        self.UndoButton = self.logic.get("UndoButton")
        self.UndoButton.connect('clicked()', self.UndoButtonClicked)
        # -------------------------------- PLANES --------------------------------#
        self.CollapsibleButton3 = self.logic.get("CollapsibleButton3")
        self.save = self.logic.get("save")
        self.read = self.logic.get("read")
        self.save.connect('clicked(bool)', self.savePlane)
        self.read.connect('clicked(bool)', self.readPlane)
        #-------------------- onCloseScene ----------------------#
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

    def onCloseScene(self, obj, event):
        self.colorSliceVolumes = dict()
        for key in self.logic.ColorNodeCorrespondence:
            self.logic.planeDict[self.logic.ColorNodeCorrespondence[key]] = self.logic.planeDef()
        self.UndoButton.enabled = False


    def enter(self):
        if self.autoChangeLayout.isChecked():
            lm = slicer.app.layoutManager()
            self.currentLayout = lm.layout
            lm.setLayout(4)  # 3D-View
        # Show manual planes
        for planeControls in self.planeControlsDictionary.values():
            if planeControls.PlaneIsDefined():
                planeControls.logic.planeLandmarks(planeControls.landmark1ComboBox.currentIndex, planeControls.landmark2ComboBox.currentIndex,
                                          planeControls.landmark3ComboBox.currentIndex, planeControls.slider.value, planeControls.slideOpacity.value)

        # Checking the names of the fiducials
        list = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
        end = list.GetNumberOfItems()
        for i in range(0,end):
            fidList = list.GetItemAsObject(i)
            landmarkDescription = self.logic.decodeJSON(fidList.GetAttribute("landmarkDescription"))
            if landmarkDescription:
                for n in range(fidList.GetNumberOfMarkups()):
                    markupID = fidList.GetNthMarkupID(n)
                    markupLabel = fidList.GetNthMarkupLabel(n)
                    landmarkDescription[markupID]["landmarkLabel"] = markupLabel
                fidList.SetAttribute("landmarkDescription",self.logic.encodeJSON(landmarkDescription))
        self.onComputeBox()

    def exit(self):
        # Remove hidden nodes that are created just for Angle Planes
        for x in self.colorSliceVolumes.values():
            node = slicer.mrmlScene.GetNodeByID(x)
            slicer.mrmlScene.RemoveNode(node)
            node.SetHideFromEditors(False)
        self.colorSliceVolumes = dict()
        # Hide manual planes
        for planeControls in self.planeControlsDictionary.values():
            if planeControls.PlaneIsDefined():
                planeControls.logic.planeLandmarks(planeControls.landmark1ComboBox.currentIndex, planeControls.landmark2ComboBox.currentIndex,
                                          planeControls.landmark3ComboBox.currentIndex, planeControls.slider.value, 0)
        # Hide planes
        for x in self.logic.ColorNodeCorrespondence.keys():
            compNode = slicer.util.getNode('vtkMRMLSliceCompositeNode' + x)
            compNode.SetLinkedControl(False)
            slice = slicer.mrmlScene.GetNodeByID(self.logic.ColorNodeCorrespondence[x])
            slice.SetWidgetVisible(False)
            slice.SetSliceVisible(False)
        # Reset layout
        if self.autoChangeLayout.isChecked():
            lm = slicer.app.layoutManager()
            if lm.layout == 4:  # the user has not manually changed the layout
                lm.setLayout(self.currentLayout)

    def savePlane(self):
        self.logic.getCoord()
        self.logic.saveFunction()

    def readPlane(self):
        self.logic.readPlaneFunction(self.red_plane_box, self.yellow_plane_box, self.green_plane_box)

    def UndoButtonClicked(self):
        print "undo:"
        print self.dictionnaryModel
        self.UndoButton.enabled = False
        for key,value in self.dictionnaryModel.iteritems():
            model = slicer.mrmlScene.GetNodeByID(key)
            model.SetAndObservePolyData(value)
        for key,value in self.hardenModelIDdict.iteritems():
            fidList = slicer.mrmlScene.GetNodeByID(key)
            fidList.SetAttribute("hardenModelID", value)
        for key,value in self.modelIDdict.iteritems():
            fidList = slicer.mrmlScene.GetNodeByID(key)
            fidList.SetAttribute("connectedModelID", value)
        for key,value in self.landmarkDescriptionDict.iteritems():
            fidList = slicer.mrmlScene.GetNodeByID(key)
            fidList.SetAttribute("landmarkDescription",value)

    def onComputeBox(self):
        #--------------------------- Box around the model --------------------------#
        positionOfVisibleNodes = self.getPositionOfModelNodes(True)
        if len(positionOfVisibleNodes) == 0:
            return
        try:
            maxValue = slicer.sys.float_info.max
        except:
            maxValue = self.logic.sys.float_info.max
        bound = [maxValue, -maxValue, maxValue, -maxValue, maxValue, -maxValue]
        for i in positionOfVisibleNodes:
            node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            model = self.logic.createIntermediateHardenModel(node)
            polydata = model.GetPolyData()
            if polydata is None or not hasattr(polydata, "GetBounds"):
                continue
            tempbound = polydata.GetBounds()
            bound[0] = min(bound[0], tempbound[0])
            bound[2] = min(bound[2], tempbound[2])
            bound[4] = min(bound[4], tempbound[4])

            bound[1] = max(bound[1], tempbound[1])
            bound[3] = max(bound[3], tempbound[3])
            bound[5] = max(bound[5], tempbound[5])
        # --------------------------- Box around the model --------------------------#
        dim = []
        origin = []
        for x in range(0, 3):
            dim.append(bound[x * 2 + 1] - bound[x * 2])
            origin.append(bound[x * 2] + dim[x] / 2)
            dim[x] *= 1.1
        dictColors = {'Red': 32, 'Yellow': 15, 'Green': 1}
        for x in dictColors.keys():
            sampleVolumeNode = self.CreateNewNode(x, dictColors[x], dim, origin)
            compNode = slicer.util.getNode('vtkMRMLSliceCompositeNode' + x)
            compNode.SetLinkedControl(False)
            compNode.SetBackgroundVolumeID(sampleVolumeNode.GetID())
        lm = slicer.app.layoutManager()
        #Reset and fit 2D-views
        lm.resetSliceViews()
        for x in dictColors.keys():
            logic = lm.sliceWidget(x)
            node = logic.mrmlSliceNode()
            node.SetSliceResolutionMode(node.SliceResolutionMatch2DView)
            logic.fitSliceToBackground()
        #Reset pink box around models
        for i in range(0, lm.threeDViewCount):
            threeDView = lm.threeDWidget(i).threeDView()
            threeDView.resetFocalPoint()
            #Reset camera in 3D view to center the models and position the camera so that all actors can be seen
            threeDView.renderWindow().GetRenderers().GetFirstRenderer().ResetCamera()

    def getPositionOfModelNodes(self, onlyVisible):
        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        positionOfNodes = list()
        for i in range(0, numNodes):
            node = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            if node.GetName() in self.ignoredNodeNames:
                continue
            if onlyVisible is True and node.GetDisplayVisibility() == 0:
                continue
            positionOfNodes.append(i)
        return positionOfNodes

    def CreateNewNode(self, colorName, color, dim, origin):
        # we add a pseudo-random number to the name of our empty volume to avoid the risk of having a volume called
        #  exactly the same by the user which could be confusing. We could also have used slicer.app.sessionId()
        if colorName not in self.colorSliceVolumes.keys():
            VolumeName = "EasyClip_EmptyVolume_" + str(slicer.app.applicationPid()) + "_" + colorName
            # Do NOT set the spacing and the origin of imageData (vtkImageData)
            # The spacing and the origin should only be set in the vtkMRMLScalarVolumeNode!!!!!!
            # We only create an image of 1 voxel (as we only use it to color the planes
            imageData = vtk.vtkImageData()
            imageData.SetDimensions(1, 1, 1)
            imageData.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
            imageData.SetScalarComponentFromDouble(0, 0, 0, 0, color)
            if hasattr(slicer, 'vtkMRMLLabelMapVolumeNode'):
                sampleVolumeNode = slicer.vtkMRMLLabelMapVolumeNode()
            else:
                sampleVolumeNode = slicer.vtkMRMLScalarVolumeNode()
            sampleVolumeNode = slicer.mrmlScene.AddNode(sampleVolumeNode)
            sampleVolumeNode.SetName(VolumeName)
            labelmapVolumeDisplayNode = slicer.vtkMRMLLabelMapVolumeDisplayNode()
            slicer.mrmlScene.AddNode(labelmapVolumeDisplayNode)
            colorNode = slicer.util.getNode('GenericAnatomyColors')
            labelmapVolumeDisplayNode.SetAndObserveColorNodeID(colorNode.GetID())
            sampleVolumeNode.SetAndObserveImageData(imageData)
            sampleVolumeNode.SetAndObserveDisplayNodeID(labelmapVolumeDisplayNode.GetID())
            labelmapVolumeDisplayNode.VisibilityOff()
            self.colorSliceVolumes[colorName] = sampleVolumeNode.GetID()
        sampleVolumeNode = slicer.mrmlScene.GetNodeByID(self.colorSliceVolumes[colorName])
        sampleVolumeNode.HideFromEditorsOn()
        sampleVolumeNode.SetOrigin(origin[0], origin[1], origin[2])
        sampleVolumeNode.SetSpacing(dim[0], dim[1], dim[2])
        if not hasattr(slicer, 'vtkMRMLLabelMapVolumeNode'):
            sampleVolumeNode.SetLabelMap(1)
        sampleVolumeNode.SetHideFromEditors(True)
        sampleVolumeNode.SetSaveWithScene(False)
        return sampleVolumeNode

    def ClippingButtonClicked(self):
        self.logic.getCoord()
        self.dictionnaryModel, self.modelIDdict, self.hardenModelIDdict, self.landmarkDescriptionDict\
            = self.logic.clipping()
        self.UndoButton.enabled = True

    def updateSliceState(self, plane, boxState, negState, posState):
        print "Update Slice State"
        self.logic.planeDict[plane].boxState = boxState
        self.logic.planeDict[plane].negState = negState
        self.logic.planeDict[plane].posState = posState



class EasyClipLogic(ScriptedLoadableModuleLogic):

    try:
        slicer.sys
    except:
        import sys

    class planeDef(object):
        def __init__(self):
            # Matrix that define each plane
            self.matrix = None
            # normal to the plane
            self.n = None
            # point in the plane
            self.P = None
            # Slice State
            self.boxState = False
            self.negState = False
            self.posState = False
            # Plane for cliping
            self.vtkPlane = vtk.vtkPlane()

    def __init__(self, interface):
        self.interface = interface
        self.ColorNodeCorrespondence = {'Red': 'vtkMRMLSliceNodeRed',
                                        'Yellow': 'vtkMRMLSliceNodeYellow',
                                        'Green': 'vtkMRMLSliceNodeGreen'}
        self.get_normal = numpy.matrix([[0], [0], [1], [0]])
        self.get_point = numpy.matrix([[0], [0], [0], [1]])
        self.planeDict = dict()
        for key in self.ColorNodeCorrespondence:
            self.planeDict[self.ColorNodeCorrespondence[key]] = self.planeDef()

    def get(self, objectName):
        return self.findWidget(self.interface.widget, objectName)

    def findWidget(self, widget, objectName):
        if widget.objectName == objectName:
            return widget
        else:
            for w in widget.children():
                resulting_widget = self.findWidget(w, objectName)
                if resulting_widget:
                    return resulting_widget
            return None

    def createIntermediateHardenModel(self, model):
        hardenModel = slicer.mrmlScene.GetNodesByName("SurfaceRegistration_" + model.GetName() + "_hardenCopy_" + str(
            slicer.app.applicationPid())).GetItemAsObject(0)
        if hardenModel is None:
            hardenModel = slicer.vtkMRMLModelNode()
        hardenPolyData = vtk.vtkPolyData()
        hardenPolyData.DeepCopy(model.GetPolyData())
        hardenModel.SetAndObservePolyData(hardenPolyData)
        hardenModel.SetName(
            "SurfaceRegistration_" + model.GetName() + "_hardenCopy_" + str(slicer.app.applicationPid()))
        if model.GetParentTransformNode():
            hardenModel.SetAndObserveTransformNodeID(model.GetParentTransformNode().GetID())
        hardenModel.HideFromEditorsOn()
        slicer.mrmlScene.AddNode(hardenModel)
        logic = slicer.vtkSlicerTransformLogic()
        logic.hardenTransform(hardenModel)
        return hardenModel

    def onCheckBoxClicked(self, colorPlane, checkBox, radioButton ):
        slice = slicer.util.getNode(self.ColorNodeCorrespondence[colorPlane])
        print "Slice test", slice
        if checkBox.isChecked():
            slice.SetWidgetVisible(True)
            radioButton.setChecked(True)
        else:
            slice.SetWidgetVisible(False)

    def getMatrix(self, slice):
        mat = slice.GetSliceToRAS()
        m = numpy.matrix([[mat.GetElement(0, 0), mat.GetElement(0, 1), mat.GetElement(0, 2), mat.GetElement(0, 3)],
                          [mat.GetElement(1, 0), mat.GetElement(1, 1), mat.GetElement(1, 2), mat.GetElement(1, 3)],
                          [mat.GetElement(2, 0), mat.GetElement(2, 1), mat.GetElement(2, 2), mat.GetElement(2, 3)],
                          [mat.GetElement(3, 0), mat.GetElement(3, 1), mat.GetElement(3, 2), mat.GetElement(3, 3)]])
        return m

    def getCoord(self):
        for key, planeDef in self.planeDict.iteritems():
            planeDef.matrix = self.getMatrix(slicer.util.getNode(key))
            planeDef.n = planeDef.matrix * self.get_normal
            # print "n : \n", planeDef.n
            planeDef.P = planeDef.matrix * self.get_point

            # print "P : \n", planeDef.P
            a = planeDef.n[0]
            b = planeDef.n[1]
            c = planeDef.n[2]
            d = planeDef.n[0]*planeDef.P[0] + planeDef.n[1]*planeDef.P[1] + planeDef.n[2]*planeDef.P[2]
            # print key + "plan equation : \n", a ,"* x + ", b , "* y + ", c , "* z - ", d ," = 0 "


    def clipping(self):
        planeCollection = vtk.vtkPlaneCollection()
        harden = slicer.vtkSlicerTransformLogic()
        tempTransform = slicer.vtkMRMLLinearTransformNode()
        tempTransform.HideFromEditorsOn()
        slicer.mrmlScene.AddNode(tempTransform)
        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        dictionnaryModel = dict()
        hardenModelIDdict = dict()
        landmarkDescriptionDict = dict()
        modelIDdict = dict()
        for i in range(3, numNodes):
            planeCollection.RemoveAllItems()
            mh = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            if mh.GetDisplayVisibility() == 0:
                continue
            model = slicer.util.getNode(mh.GetName())
            transform = model.GetParentTransformNode()
            if transform:
                tempTransform.Copy(transform)
                harden.hardenTransform(tempTransform)
                m = vtk.vtkMatrix4x4()
                tempTransform.GetMatrixTransformToParent(m)
                m.Invert(m, m)
            else:
                m = vtk.vtkMatrix4x4()
            for key, planeDef in self.planeDict.iteritems():
                hardenP = m.MultiplyPoint(planeDef.P)
                hardenN = m.MultiplyPoint(planeDef.n)
                if planeDef.boxState:
                    planeDef.vtkPlane.SetOrigin(hardenP[0], hardenP[1], hardenP[2])
                    if planeDef.negState:
                        planeDef.vtkPlane.SetNormal(-hardenN[0], -hardenN[1], -hardenN[2])
                    if planeDef.posState:
                        planeDef.vtkPlane.SetNormal(hardenN[0], hardenN[1], hardenN[2])
                    planeCollection.AddItem(planeDef.vtkPlane)
            dictionnaryModel[model.GetID()]= model.GetPolyData()
            polyData = model.GetPolyData()
            clipper = vtk.vtkClipClosedSurface()
            clipper.SetClippingPlanes(planeCollection)
            clipper.SetInputData(polyData)
            clipper.SetGenerateFaces(1)
            clipper.SetScalarModeToLabels()
            clipper.Update()
            polyDataNew = clipper.GetOutput()
            model.SetAndObservePolyData(polyDataNew)
            # Checking if one ore more fiducial list are connected to this model
            list = slicer.mrmlScene.GetNodesByClass("vtkMRMLMarkupsFiducialNode")
            end = list.GetNumberOfItems()
            for i in range(0,end):
                fidList = list.GetItemAsObject(i)
                if fidList.GetAttribute("connectedModelID"):
                    if fidList.GetAttribute("connectedModelID") == model.GetID():
                        modelIDdict[fidList.GetID()], hardenModelIDdict[fidList.GetID()], landmarkDescriptionDict[fidList.GetID()] = \
                            self.unprojectLandmarks(fidList)
        return dictionnaryModel, modelIDdict, hardenModelIDdict, landmarkDescriptionDict

    def unprojectLandmarks(self, fidList):
        hardenModelID = fidList.GetAttribute("hardenModelID")
        ModelID = fidList.GetAttribute("connectedModelID")
        landmarkDescriptioncopy = fidList.GetAttribute("landmarkDescription")
        fidList.SetAttribute("connectedModelID", None)
        fidList.SetAttribute("hardenModelID", None)
        landmarkDescription = self.decodeJSON(fidList.GetAttribute("landmarkDescription"))
        for n in range(fidList.GetNumberOfMarkups()):
            markupID = fidList.GetNthMarkupID(n)
            landmarkDescription[markupID]["projection"]["isProjected"] = False
            landmarkDescription[markupID]["projection"]["closestPointIndex"] = None
            landmarkDescription[markupID]["ROIradius"] = 0
        fidList.SetAttribute("landmarkDescription",self.encodeJSON(landmarkDescription))
        return ModelID, hardenModelID, landmarkDescriptioncopy


    def saveFunction(self):
        filename = qt.QFileDialog.getSaveFileName(parent=self,caption='Save file')
        tempDictionary = {}
        for key in self.ColorNodeCorrespondence:
            slice = slicer.util.getNode(self.ColorNodeCorrespondence[key])
            tempDictionary[key] = self.getMatrix(slice).tolist()
        if filename is None:
            filename = qt.QFileDialog.getSaveFileName(parent=self, caption='Save file')
        if filename != "":
            fileObj = open(filename, "wb")
            pickle.dump(tempDictionary, fileObj)
            fileObj.close()

    def readPlaneFunction(self, red_plane_box, yellow_plane_box, green_plane_box):
        filename = qt.QFileDialog.getOpenFileName(parent=self,caption='Open file')
        if filename is None:
            filename = qt.QFileDialog.getOpenFileName(parent=self, caption='Open file')
        if filename != "":
            fileObj = open(filename, "rb")
            tempDictionary = pickle.load(fileObj)
            for key in self.ColorNodeCorrespondence:
                node = slicer.mrmlScene.GetNodeByID(self.ColorNodeCorrespondence[key])
                matList = tempDictionary[key]
                matNode = node.GetSliceToRAS()
                for col in range(0, len(matList)):
                    for row in range(0, len(matList[col])):
                        matNode.SetElement(col, row, matList[col][row])
            fileObj.close()

    def encodeJSON(self, input):
        encodedString = json.dumps(input)
        encodedString = encodedString.replace('\"', '\'')
        return encodedString

    def decodeJSON(self, input):
        if input:
            input = input.replace('\'','\"')
            return self.byteify(json.loads(input))
        return None

    def byteify(self, input):
        if isinstance(input, dict):
            return {self.byteify(key):self.byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [self.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input

class EasyClipTest(ScriptedLoadableModuleTest):
    def setUp(self):
        # reset the state - clear scene
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        # run all tests needed
        self.setUp()
        self.test_EasyClip()

    def test_EasyClip(self):

        self.delayDisplay("Starting the test")
        ###################################################################################################
        #                                        Loading some data                                        #
        ###################################################################################################
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=167065', 'model.vtk', slicer.util.loadModel),
            )

        for url,name,loader in downloads:
          filePath = slicer.app.temporaryPath + '/' + name
          if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
            print('Requesting download %s from %s...\n' % (name, url))
            urllib.urlretrieve(url, filePath)
          if loader:
            print('Loading %s...\n' % (name,))
            loader(filePath)
        self.delayDisplay('Finished with download and loading\n')


        layoutManager = slicer.app.layoutManager()
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()

        self.delayDisplay('Model loaded')

        ###################################################################################################
        #                                 Initialize Plane Position                                       #
        ###################################################################################################

        redslice = slicer.util.getNode('vtkMRMLSliceNodeRed')
        yellowslice = slicer.util.getNode('vtkMRMLSliceNodeYellow')
        greenslice = slicer.util.getNode('vtkMRMLSliceNodeGreen')
        # print redslice, yellowslice, greenslice
        self.delayDisplay('Planes are displayed!')

        #Put planes at specific places
        matRed = redslice.GetSliceToRAS()

        matRed.SetElement(0,3,0)
        matRed.SetElement(1,3,0)
        matRed.SetElement(2,3,8)
        redslice.SetWidgetVisible(True)
        print matRed

        matYellow = yellowslice.GetSliceToRAS()
        matYellow.SetElement(0,3,-3)
        matYellow.SetElement(1,3,0)
        matYellow.SetElement(2,3,0)
        print matYellow
        yellowslice.SetWidgetVisible(True)

        matGreen = greenslice.GetSliceToRAS()
        matGreen.SetElement(0,3,0)
        matGreen.SetElement(1,3,-9)
        matGreen.SetElement(2,3,0)
        print matGreen
        greenslice.SetWidgetVisible(True)

        self.delayDisplay('planes are placed!')

        logic = EasyClipLogic()
        logic.getCoord()
        logic.clipping(True, False, True, False, False, False, False, False, False)


        print 'DONE'

        self.delayDisplay('Test passed!')

