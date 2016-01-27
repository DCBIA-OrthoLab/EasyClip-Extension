from __main__ import vtk, qt, ctk, slicer
import numpy
import SimpleITK as sitk
from slicer.ScriptedLoadableModule import *
import os

#
# Load Files
#

class EasyClip(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        parent.title = "Easy Clip"
        parent.categories = ["Shape Analysis"]
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
        print "-------Setup---------"

        self.planeControlsDictionary = {}
        # Instantiate and connect widgets
        #
        # Interface
        #
        # Collapsible button -- Scene Description
        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Scene"
        self.layout.addWidget(self.loadCollapsibleButton)
        self.ignoredNodeNames = ('Red Volume Slice', 'Yellow Volume Slice', 'Green Volume Slice')
        self.colorSliceVolumes = dict()

        # Layout within the laplace collapsible button
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        # GLOBALS:
        self.image = None
        self.logic = EasyClipLogic()
        #--------------------------- List of Models --------------------------#

        treeView = slicer.qMRMLTreeView()
        treeView.setMRMLScene(slicer.app.mrmlScene())
        treeView.setSceneModelType('Displayable')
        treeView.sceneModel().setHorizontalHeaderLabels(["Models"])
        treeView.sortFilterProxyModel().nodeTypes = ['vtkMRMLModelNode']
        header = treeView.header()
        header.setResizeMode(0, qt.QHeaderView.Stretch)
        header.setVisible(True)
        self.loadFormLayout.addWidget(treeView)

        self.autoChangeLayout = qt.QCheckBox()
        self.autoChangeLayout.setCheckState(qt.Qt.Checked)
        self.autoChangeLayout.setTristate(False)
        self.autoChangeLayout.setText("Automatically change layout to 3D only")
        self.loadFormLayout.addWidget(self.autoChangeLayout)
        # Add vertical spacer
        self.layout.addStretch(1)
        #------------------------ Compute Bounding Box ----------------------#
        buttonFrameBox = qt.QFrame(self.parent)
        buttonFrameBox.setLayout(qt.QHBoxLayout())
        self.loadFormLayout.addWidget(buttonFrameBox)

        self.computeBox = qt.QPushButton("Compute Bounding Box around all models")
        buttonFrameBox.layout().addWidget(self.computeBox)
        self.computeBox.connect('clicked()', self.onComputeBox)

        #--------------------------- Clipping Part --------------------------#

        # Collapsible button -- Clipping part
        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Clipping"
        self.layout.addWidget(self.loadCollapsibleButton)

        # Layout within the laplace collapsible button
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        #-------------------------- Buttons --------------------------#
        # CLIPPING BUTTONS

        self.red_plane_box = qt.QGroupBox("Red Slice Clipping")
        self.red_plane_box.setCheckable(True)
        self.red_plane_box.setChecked(False)
        self.radio_red_Neg = qt.QRadioButton("Keep Down Arrow")
        self.radio_red_Neg.setIcon(qt.QIcon(":/Icons/RedSpaceNegative.png"))
        self.radio_red_Pos = qt.QRadioButton("Keep Top Arrow")
        self.radio_red_Pos.setIcon(qt.QIcon(":/Icons/RedSpacePositive.png"))
        self.red_plane_box.connect('clicked(bool)', self.redPlaneCheckBoxClicked)
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


        vbox = qt.QHBoxLayout()
        vbox.addWidget(self.radio_red_Neg)
        vbox.addWidget(self.radio_red_Pos)
        vbox.addStretch(1)
        self.red_plane_box.setLayout(vbox)
        self.loadFormLayout.addWidget(self.red_plane_box)

        self.yellow_plane_box = qt.QGroupBox("Yellow Slice Clipping")
        self.yellow_plane_box.setCheckable(True)
        self.yellow_plane_box.setChecked(False)
        self.yellow_plane_box.connect('clicked(bool)', self.yellowPlaneCheckBoxClicked)

        self.radio_yellow_Neg= qt.QRadioButton("Keep Down Arrow")
        self.radio_yellow_Neg.setIcon(qt.QIcon(":/Icons/YellowSpaceNegative.png"))
        self.radio_yellow_Pos = qt.QRadioButton("Keep Top Arrow")
        self.radio_yellow_Pos.setIcon(qt.QIcon(":/Icons/YellowSpacePositive.png"))
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


        vbox = qt.QHBoxLayout()
        vbox.addWidget(self.radio_yellow_Neg)
        vbox.addWidget(self.radio_yellow_Pos)
        vbox.addStretch(1)
        self.yellow_plane_box.setLayout(vbox)
        self.loadFormLayout.addWidget(self.yellow_plane_box)


        self.green_plane_box = qt.QGroupBox("Green Slice Clipping")
        self.green_plane_box.setCheckable(True)
        self.green_plane_box.setChecked(False)
        self.green_plane_box.connect('clicked(bool)', self.greenPlaneCheckBoxClicked)

        self.radio_green_Neg= qt.QRadioButton("Keep Down Arrow")
        self.radio_green_Neg.setIcon(qt.QIcon(":/Icons/GreenSpaceNegative.png"))
        self.radio_green_Pos = qt.QRadioButton("Keep Top Arrow")
        self.radio_green_Pos.setIcon(qt.QIcon(":/Icons/GreenSpacePositive.png"))
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


        vbox = qt.QHBoxLayout()
        vbox.addWidget(self.radio_green_Neg)
        vbox.addWidget(self.radio_green_Pos)
        vbox.addStretch(1)
        self.green_plane_box.setLayout(vbox)
        self.loadFormLayout.addWidget(self.green_plane_box)

        buttonFrame = qt.QFrame(self.parent)
        buttonFrame.setLayout(qt.QHBoxLayout())
        self.loadFormLayout.addWidget(buttonFrame)

        self.ClippingButton = qt.QPushButton("Clipping")
        buttonFrame.layout().addWidget(self.ClippingButton)
        self.ClippingButton.connect('clicked()', self.ClippingButtonClicked)

        self.UndoButton = qt.QPushButton("Undo")
        buttonFrame.layout().addWidget(self.UndoButton)
        self.UndoButton.connect('clicked()', self.UndoButtonClicked)

        #--------------------------- Advanced Part --------------------------#
        #-------------------- Collapsible button -- Clipping part ----------------------#

        self.loadCollapsibleButton = ctk.ctkCollapsibleButton()
        self.loadCollapsibleButton.text = "Planes"
        self.layout.addWidget(self.loadCollapsibleButton)

        #-------------------- Layout within the laplace collapsible button ----------------------#
        self.loadFormLayout = qt.QFormLayout(self.loadCollapsibleButton)

        buttonFrame = qt.QFrame(self.parent)
        buttonFrame.setLayout(qt.QVBoxLayout())
        self.loadFormLayout.addWidget(buttonFrame)

        #-------------------- SAVE PLANE BUTTON ----------------------#

        save_plane = qt.QLabel("Save the planes you create as a txt file.")
        buttonFrame.layout().addWidget(save_plane)
        save = qt.QPushButton("Save plane")
        buttonFrame.layout().addWidget(save)
        save.connect('clicked(bool)', self.savePlane)

        #-------------------- READ PLANE BUTTON ----------------------#

        load_plane = qt.QLabel("Load the file with the plane you saved.")
        buttonFrame.layout().addWidget(load_plane)
        read = qt.QPushButton("Load plane")
        buttonFrame.layout().addWidget(read)
        read.connect('clicked(bool)', self.readPlane)

        #-------------------- Add vertical spacer ----------------------#
        self.layout.addStretch(1)

        #-------------------- onCloseScene ----------------------#
        slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)

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

    def redPlaneCheckBoxClicked(self):
        self.logic.onCheckBoxClicked('Red', self.red_plane_box, self.radio_red_Neg)

    def yellowPlaneCheckBoxClicked(self):
        self.logic.onCheckBoxClicked('Yellow', self.yellow_plane_box, self.radio_yellow_Neg)

    def greenPlaneCheckBoxClicked(self):
        self.logic.onCheckBoxClicked('Green', self.green_plane_box,  self.radio_green_Neg)

    def savePlane(self):
        self.logic.getCoord()
        self.logic.saveFunction()

    def readPlane(self):
        self.logic.readPlaneFunction(self.red_plane_box, self.yellow_plane_box, self.green_plane_box)

    def UndoButtonClicked(self):
        for key,value in self.dictionnaryModel.iteritems():
            model = slicer.mrmlScene.GetNodeByID(key)
            model.SetAndObservePolyData(value)

    def onCloseScene(self, obj, event):
        globals()["EasyClip"] = slicer.util.reloadScriptedModule("EasyClip")
        if self.image:
            self.image.__del__()

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
            polydata = node.GetPolyData()
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
        print dim
        print origin

        dictColors = {'Red': 32, 'Yellow': 15, 'Green': 1}
        for x in dictColors.keys():
            sampleVolumeNode = self.CreateNewNode(x, dictColors[x], dim, origin)
            compNode = slicer.util.getNode('vtkMRMLSliceCompositeNode' + x)
            compNode.SetLinkedControl(False)
            compNode.SetBackgroundVolumeID(sampleVolumeNode.GetID())
            print "set background" + x
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
        sampleVolumeNode.SetOrigin(origin[0], origin[1], origin[2])
        sampleVolumeNode.SetSpacing(dim[0], dim[1], dim[2])
        if not hasattr(slicer, 'vtkMRMLLabelMapVolumeNode'):
            sampleVolumeNode.SetLabelMap(1)
        sampleVolumeNode.SetHideFromEditors(True)
        sampleVolumeNode.SetSaveWithScene(False)
        return sampleVolumeNode

    def ClippingButtonClicked(self):
        self.logic.getCoord()
        self.dictionnaryModel = self.logic.clipping()

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

    def __init__(self):
        self.ColorNodeCorrespondence = {'Red': 'vtkMRMLSliceNodeRed',
                                        'Yellow': 'vtkMRMLSliceNodeYellow',
                                        'Green': 'vtkMRMLSliceNodeGreen'}
        self.get_normal = numpy.matrix([[0], [0], [1], [0]])
        self.get_point = numpy.matrix([[0], [0], [0], [1]])
        self.planeDict = dict()
        for key in self.ColorNodeCorrespondence:
            self.planeDict[self.ColorNodeCorrespondence[key]] = self.planeDef()

    def onCheckBoxClicked(self, colorPlane, checkBox, radioButton ):
        slice = slicer.util.getNode(self.ColorNodeCorrespondence[colorPlane])
        print "Slice test", slice
        if checkBox.isChecked():
            slice.SetWidgetVisible(True)
            radioButton.setChecked(True)
        else:
            slice.SetWidgetVisible(False)

    def computeBoxFunction(self, image):
        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        for i in range(3, numNodes):
            elements = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode" )
            print elements.GetName()
        node = slicer.util.getNode(elements.GetName())
        polydata = node.GetPolyData()
        bound = polydata.GetBounds()
        print "bound", bound

        dimX = bound[1]-bound[0]
        dimY = bound[3]-bound[2]
        dimZ = bound[5]-bound[4]

        print "dimension X :", dimX
        print "dimension Y :", dimY
        print "dimension Z :", dimZ

        dimX = dimX + 10
        dimY = dimY + 20
        dimZ = dimZ + 20

        center = polydata.GetCenter()
        print "Center polydata :", center

        # Creation of an Image
        image = sitk.Image(int(dimX), int(dimY), int(dimZ), sitk.sitkInt16)

        dir = (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)
        image.SetDirection(dir)

        spacing = (1,1,1)
        image.SetSpacing(spacing)

        tab = [-center[0]+dimX/2,-center[1]+dimY/2,center[2]-dimZ/2]
        print tab
        image.SetOrigin(tab)


        writer = sitk.ImageFileWriter()
        tempPath = slicer.app.temporaryPath
        filename = "Box.nrrd"
        filenameFull=os.path.join(tempPath, filename)
        print filenameFull
        writer.SetFileName(str(filenameFull))
        writer.Execute(image)


        slicer.util.loadVolume(filenameFull)

        #------------------------ Slice Intersection Visibility ----------------------#
        numDisplayNode = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelDisplayNode")
        for i in range (3,numDisplayNode):
            slice = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelDisplayNode" )
            slice.SetSliceIntersectionVisibility(1)

        return image

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
            print "n : \n", planeDef.n
            planeDef.P = planeDef.matrix * self.get_point
            print "P : \n", planeDef.P
            a = planeDef.n[0]
            b = planeDef.n[1]
            c = planeDef.n[2]
            d = planeDef.n[0]*planeDef.P[0] + planeDef.n[1]*planeDef.P[1] + planeDef.n[2]*planeDef.P[2]
            print key + "plan equation : \n", a ,"* x + ", b , "* y + ", c , "* z - ", d ," = 0 "


    def clipping(self):

        self.planeCollection = vtk.vtkPlaneCollection()
        for key, planeDef in self.planeDict.iteritems():
            if planeDef.boxState:
                planeDef.vtkPlane.SetOrigin(planeDef.P[0], planeDef.P[1], planeDef.P[2])
                if planeDef.negState:
                    planeDef.vtkPlane.SetNormal(-planeDef.n[0], -planeDef.n[1], -planeDef.n[2])
                if planeDef.posState:
                    planeDef.vtkPlane.SetNormal(planeDef.n[0], planeDef.n[1], planeDef.n[2])
                self.planeCollection.AddItem(planeDef.vtkPlane)

        numNodes = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
        self.dictionnaryModel = dict()
        self.dictionnaryModel.clear()
        for i in range(3, numNodes):
            mh = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
            self.model = slicer.util.getNode(mh.GetName())
            self.dictionnaryModel[self.model.GetID()]=self.model.GetPolyData()
            self.polyData = self.model.GetPolyData()
            PolyAlgorithm = vtk.vtkClipClosedSurface()
            PolyAlgorithm.SetInputData(self.polyData)
            clipper = vtk.vtkClipClosedSurface()
            clipper.SetClippingPlanes(self.planeCollection)
            clipper.SetInputConnection(PolyAlgorithm.GetOutputPort())
            clipper.SetGenerateFaces(1)
            clipper.SetScalarModeToLabels()
            clipper.Update()
            polyDataNew = clipper.GetOutput()
            self.model.SetAndObservePolyData(polyDataNew)
        return self.dictionnaryModel


    def saveFunction(self):
        filename = qt.QFileDialog.getSaveFileName(parent=self,caption='Save file')
        fichier = open(filename, "w")
        fichier.write("SliceToRAS Red Slice: \n")
        fichier.write(str(self.m_Red) + '\n')
        fichier.write('\n')

        fichier.write("SliceToRAS Yellow Slice: \n")
        fichier.write(str(self.m_Yellow) + '\n')
        fichier.write('\n')

        fichier.write("SliceToRAS Green Slice: \n")
        fichier.write(str(self.m_Green) + '\n')
        fichier.write('\n')

        fichier.write("Coefficients for the Red plane: \n")
        fichier.write("a:" + str(self.a_red) + '\n')
        fichier.write("b:" + str(self.b_red) + '\n')
        fichier.write("c:" + str(self.c_red) + '\n')
        fichier.write("d:" + str(self.d_red) + '\n')

        fichier.write('\n')
        fichier.write("Coefficients for the Yellow plane: \n")
        fichier.write("a:" + str(self.a_yellow) + '\n')
        fichier.write("b:" + str(self.b_yellow) + '\n')
        fichier.write("c:" + str(self.c_yellow) + '\n')
        fichier.write("d:" + str(self.d_yellow) + '\n')

        fichier.write('\n')
        fichier.write("Coefficients for the Green plane: \n")
        fichier.write("a:" + str(self.a_green) + '\n')
        fichier.write("b:" + str(self.b_green) + '\n')
        fichier.write("c:" + str(self.c_green) + '\n')
        fichier.write("d:" + str(self.d_green) + '\n')


        fichier.close()

    def readPlaneFunction(self, red_plane_box, yellow_plane_box, green_plane_box):
        filename = qt.QFileDialog.getOpenFileName(parent=self,caption='Open file')
        print 'filename:', filename
        fichier2 = open(filename, 'r')
        fichier2.readline()
        NodeRed = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeRed')
        matRed = NodeRed.GetSliceToRAS()

        for i in range(0, 4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matRed.SetElement(i, j, float(items[j]))


        print matRed
        compare_red = 0
        self.matRed_init = numpy.matrix([[-1,0,0,0],
                                         [0,1,0,0],
                                         [0,0,1,0],
                                         [0,0,0,1]])
        print "self.matRed_init", self.matRed_init
        for i in range(0,4):
            for j in range(0,4):
                if matRed.GetElement(i,j) == self.matRed_init[i,j]:
                    compare_red = compare_red + 1

        print compare_red

        if compare_red != 16:
            self.redslice = slicer.util.getNode('vtkMRMLSliceNodeRed')
            if red_plane_box.isChecked():
                red_plane_box.setChecked(False)
                self.redslice.SetWidgetVisible(False)
            red_plane_box.setChecked(True)
            # widget.redPlaneCheckBoxClicked()
            self.redslice.SetWidgetVisible(True)

        fichier2.readline()
        fichier2.readline()


        self.matYellow_init = numpy.matrix([[0,0,1,0],
                                            [-1,0,0,0],
                                            [0,1,0,0],
                                            [0,0,0,1]])
        NodeYellow = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeYellow')
        matYellow = NodeYellow.GetSliceToRAS()
        for i in range(0, 4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matYellow.SetElement(i, j, float(items[j]))


        print matYellow

        compare_yellow = 0
        for i in range(0,4):
            for j in range(0,4):
                if matYellow.GetElement(i,j) == self.matYellow_init[i,j]:
                    compare_yellow = compare_yellow + 1

        print compare_yellow

        if compare_yellow != 16:
            self.yellowslice = slicer.util.getNode('vtkMRMLSliceNodeYellow')
            if yellow_plane_box.isChecked():
                yellow_plane_box.setChecked(False)
                self.yellowslice.SetWidgetVisible(False)

            yellow_plane_box.setChecked(True)
            # self.yellowPlaneCheckBoxClicked()
            self.yellowslice.SetWidgetVisible(True)

        fichier2.readline()
        fichier2.readline()

        self.matGreen_init = numpy.matrix([[-1,0,0,0],
                                           [0,0,1,0],
                                           [0,1,0,0],
                                           [0,0,0,1]])
        NodeGreen = slicer.mrmlScene.GetNodeByID('vtkMRMLSliceNodeGreen')
        matGreen = NodeGreen.GetSliceToRAS()
        for i in range (0,4):
            ligne = fichier2.readline()
            ligne = ligne.replace('[', '')
            ligne = ligne.replace('   ', ' ')
            ligne = ligne.replace(']', '')
            ligne = ligne.replace('\n', '')
            print ligne
            items = ligne.split()
            print items
            for j in range(0, 4):
                matGreen.SetElement(i, j, float(items[j]))


        print matGreen


        compare_green = 0
        for i in range(0,4):
            for j in range(0,4):
                if matGreen.GetElement(i,j) == self.matGreen_init[i,j]:
                    compare_green = compare_green + 1

        print compare_green

        if compare_green != 16:
            self.greenslice = slicer.util.getNode('vtkMRMLSliceNodeGreen')
            if green_plane_box.isChecked():
                green_plane_box.setChecked(False)
                self.greenslice.SetWidgetVisible(False)

            green_plane_box.setChecked(True)
            # self.greenPlaneCheckBoxClicked()
            self.greenslice.SetWidgetVisible(True)

        fichier2.close()

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

        image = None

        logic = EasyClipLogic()
        image = logic.computeBoxFunction(image)
        logic.getCoord()
        logic.clipping(True, False, True, False, False, False, False, False, False)


        print 'DONE'

        self.delayDisplay('Test passed!')

