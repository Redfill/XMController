from __future__ import division
##########################################
##                                      ##
##    XM_ctrl_placer.py - python script ##
##                                      ##
##########################################
##
## Copyright 2021 Xavier Magher
##
## DESCRIPTION:	 
##    quicly setup controllers located in the ctrl_placer_plugin folder

import maya.cmds as cmds
import maya.OpenMaya as om
from functools import partial



def getKnots(crvShape=None):
    mObj = om.MObject()
    sel = om.MSelectionList()
    sel.add(crvShape)
    sel.getDependNode(0, mObj)

    fnCurve = om.MFnNurbsCurve(mObj)
    tmpKnots = om.MDoubleArray()
    fnCurve.getKnots(tmpKnots)

    return [tmpKnots[i] for i in range(tmpKnots.length())]

def validateCurve(crv=None):
    '''Checks whether the transform we are working with is actually a curve and returns it's shapes'''
    if cmds.nodeType(crv) == "transform" and cmds.nodeType(cmds.listRelatives(crv, c=1, s=1)[0]) == "nurbsCurve":
        crvShapes = cmds.listRelatives(crv, c=1, s=1)
    elif cmds.nodeType(crv) == "nurbsCurve":
        crvShapes = cmds.listRelatives(cmds.listRelatives(crv, p=1)[0], c=1, s=1)
    else:
        cmds.error("The object " + crv + " passed to validateCurve() is not a curve")
    return crvShapes


def getShape(crv=None):
    '''Returns a dictionary containing all the necessery information for rebuilding the passed in crv.'''
    crvShapes = validateCurve(crv)

    crvShapeList = []

    for crvShape in crvShapes:
        crvShapeDict = {
            "points": [],
            "knots": [],
            "form": cmds.getAttr(crvShape + ".form"),
            "degree": cmds.getAttr(crvShape + ".degree"),
            "colour": cmds.getAttr(crvShape + ".overrideColor")
        }
        points = []

        for i in range(cmds.getAttr(crvShape + ".controlPoints", s=1)):
        	points.append(cmds.getAttr(crvShape + ".controlPoints[%i]" % i)[0])

        crvShapeDict["points"] = points
        crvShapeDict["knots"] = getKnots(crvShape)

        crvShapeList.append(crvShapeDict)

    return crvShapeList


def setShape(crv, crvShapeList):
    '''Creates a new shape on the crv transform, using the properties in the crvShapeDict.'''
    crvShapes = validateCurve(crv)

    oldColour = cmds.getAttr(crvShapes[0] + ".overrideColor")
    cmds.delete(crvShapes)

    for i, crvShapeDict in enumerate(crvShapeList):
        tmpCrv = cmds.curve(p=crvShapeDict["points"], k=crvShapeDict["knots"], d=crvShapeDict["degree"], per=bool(crvShapeDict["form"]))
        newShape = cmds.listRelatives(tmpCrv, s=1)[0]
        cmds.parent(newShape, crv, r=1, s=1)

        cmds.delete(tmpCrv)
        newShape = cmds.rename(newShape, crv + "Shape" + str(i + 1).zfill(2))

        cmds.setAttr(newShape + ".overrideEnabled", 1)


def replaceCurve():
    selected = cmds.ls(sl=True)
    shapedict = getShape(selected[0])

    for sel in selected[1:]:
        setShape(sel, shapedict)


#get maya script folders
def getMayaFld(x):
    scriptFld = cmds.internalVar(usd=True)
    dir = scriptFld + "XM_ctrl_placer_plugin/"
    imgFld = dir + "ctrl_img/"
    melFld = dir + "ctrl_mel/"
    
    if x == 0:
        return dir
    elif x == 1:
        return imgFld
    elif x == 2:
        return melFld
    else:
        return "invalide"

#get controller files inside the script directory
def getCtrlFile():
    melFdl = getMayaFld(2)
    ctrlfile = cmds.getFileList(folder=getMayaFld(2))
    return ctrlfile

def XMSearch(text, buttonl, *args):
    for b in buttonl:
        search = cmds.textFieldGrp(text, q=True, text=True).lower()
        Label = cmds.iconTextButton(b, q=True, l=True).lower()
        if(Label.find(search) == -1):
            cmds.iconTextButton(b, e=True, en=False)
        else:
            cmds.iconTextButton(b, e=True, en=True)



#import and setup the controllers
def AddCtrl(but,grp,re, buffer, cont, *args):

    #variable setup
    Label = cmds.iconTextButton(but, q=True, l=True)
    g = cmds.checkBox( grp, q=True, v=True)
    r = cmds.checkBox(re, q=True, v=True)
    b = cmds.textFieldGrp(buffer, q=True, text=True)
    c = cmds.textFieldGrp(cont, q=True, text=True)

    #selected objects
    selected = cmds.ls(sl=True)
    if len(selected) == 0:
        if(g == 0):
            cmds.file((getMayaFld(2) + Label), i=True, type = "mayaBinary", mnc=True,)
        else:
            cmds.file((getMayaFld(2) + Label), i=True, type="mayaBinary", gr=True, gn=Label, mnc=True)
    #action for every selected objects
    for n in selected:
        if(g == 0):
            cmds.file((getMayaFld(2) + Label), i=True, type = "mayaBinary", mnc=True, ns="XMImported")
        else:
            cmds.file((getMayaFld(2) + Label), i=True, type="mayaBinary", gr=True, gn="XMImported:", mnc=True, ns="XMImported")
        cmds.select("XMImported:*")

        ss = cmds.ls(sl=True, tr=True)
        for s in ss:
            print(s)
            #apply buffer actions if s is a root
            if(len(cmds.ls(s, l=True)[0].split("|")) == 2):
                cmds.matchTransform(s , n,piv=True, pos=True, rot=True)
                newBuffer = n+b
                if(r == 0):
                    newBuffer = str.replace(s, "XMImported:", "")
                cmds.rename(s, newBuffer)
            else:
                newCont = n + c
                if(r == 0):
                    newCont = str.replace(s, "XMImported:", "")
                cmds.rename(s, newCont)
    
class XMctrl(object):   
    #constructor
    def __init__(self):
        
            
        self.window = "XMctrl"
        self.title = "XM crtl creator"
        self.size = (500, 500)
        #all button generated by the script
        buttonlist = []
            
        # close old window is open
        if cmds.window(self.window, exists = True):
            cmds.deleteUI(self.window, window=True)
            
        #create new window
        self.window = cmds.window(self.window, title=self.title, widthHeight=self.size)

        ch1 = cmds.columnLayout(adj=True)

        cmds.frameLayout(l="utils", cll=True, cl=True)
        cmds.button(l="replace curve", c="replaceCurve()")


        #import options

        #controller nomenclature tab
        cmds.setParent(ch1)
        cmds.frameLayout(l="nomenclature", cll=True, cl=True, bgc=(0.2,0.2,0.3))
        XMctrlBuffer = cmds.textFieldGrp(l="Buffer:", text="_ctrl_srtBuffer")
        XMctrlCont = cmds.textFieldGrp(l="Controller:", text="_ctrl")

        #controller creation tab
        cmds.setParent(ch1)
        cmds.frameLayout(l="create controller",cll=True,bgc=(0.5,0.2,0.2))
        cmds.rowLayout(nc=3, adj=True)

        ctrlSearch=cmds.textFieldGrp(l="search:", adj=True)
        cmds.textFieldGrp(ctrlSearch, e=True, cc=partial(XMSearch, ctrlSearch, buttonlist))
        CtrlGroup=cmds.checkBox(l="group", v=True)
        CtrlRename=cmds.checkBox(l="rename", v=True)


        #controllers Ui
        cmds.setParent(u=True)
        cmds.scrollLayout(h=self.size[1]/1.2)
        cmds.gridLayout( nc=4, cwh = (self.size[0]/4,self.size[1]/4) )

        #create controller buttons
        for i in getCtrlFile():
            PNGfile = str.replace(i,".mb", ".png")
            button = cmds.iconTextButton(label=i)
            buttonlist.append(button)
            cmds.iconTextButton(button, e=True, style="iconOnly", i=(getMayaFld(1) + PNGfile), ann=i, command=partial(AddCtrl, button, CtrlGroup, CtrlRename, XMctrlBuffer, XMctrlCont))
        
        

        #display new window
        cmds.showWindow()
        cmds.window(self.window,e=True, wh=(500,500))
          
XMWindow = XMctrl()