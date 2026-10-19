# SPDX-License-Identifier: GPL-3.0-only
"""Run inside the packaged FreeCAD interpreter, never in the host Python."""
import json, math, traceback
from pathlib import Path
import FreeCAD as App, FreeCADGui as Gui, Part

try:
    from fusionflow_core import extrude, cut_all
    from fusionflow_construct import create
    from PySide import QtWidgets
    doc=App.newDocument('TabletSmoke')
    doc.UndoMode=1
    bodies=[]
    for z in (0,20,40):
        body=doc.addObject('PartDesign::Body','Body')
        box=body.newObject('PartDesign::AdditiveBox','Box')
        box.Length=box.Width=box.Height=10
        box.Placement.Base.z=z
        bodies.append(body)
    sketch=doc.addObject('Sketcher::SketchObject','CutProfile')
    points=[(0,0),(5,0),(5,10),(0,10),(0,0)]
    for a,b in zip(points,points[1:]):
        sketch.addGeometry(Part.LineSegment(App.Vector(*a,0),App.Vector(*b,0)),False)
    doc.recompute()
    doc.openTransaction('Preview selected bodies')
    assert len(cut_all(sketch,[1],targets=[bodies[0],bodies[2]],extent='All'))==2
    assert all(abs(b.Shape.Volume-v)<1e-5 for b,v in zip(bodies,(500,1000,500)))
    doc.abortTransaction();doc.recompute()
    assert all(abs(b.Shape.Volume-1000)<1e-5 for b in bodies)
    doc.openTransaction('Cut selected bodies')
    cut_all(sketch,[1],targets=[bodies[0],bodies[2]],extent='All')
    doc.commitTransaction()
    middle=bodies[1]
    top=next('Face%d'%i for i,f in enumerate(middle.Shape.Faces,1) if f.normalAt(0,0).z>.99)
    joined=extrude(middle,[top],'Join',middle,length=2)
    assert abs(joined.Shape.Volume-1200)<1e-5
    top=next('Face%d'%i for i,f in enumerate(joined.Shape.Faces,1) if f.normalAt(0,0).z>.99)
    plane=create(doc,'OffsetPlane',[(joined,[top])],{'Distance':5})
    circle=doc.addObject('Sketcher::SketchObject','PlaneProfile')
    circle.AttachmentSupport=[(plane,['Face1'])];circle.MapMode='FlatFace'
    circle.addGeometry(Part.Circle(App.Vector(5,5,0),App.Vector(0,0,1),2),False)
    doc.recompute()
    assert abs(circle.Placement.Base.z-37)<1e-5
    raised=extrude(circle,[1],length=4)
    assert abs(raised.Shape.Volume-16*math.pi)<1e-5
    section=joined.Shape.section(Part.makePlane(50,50,App.Vector(-10,-10,25)))
    assert len(section.Edges)>0
    expected={b.Name:b.Shape.Volume for b in bodies}
    expected[raised.Name]=raised.Shape.Volume
    path='/home/web_user/TabletSmoke.FCStd'
    doc.saveAs(path);App.closeDocument(doc.Name)
    doc=App.openDocument(path);doc.recompute()
    for name,volume in expected.items():
        assert abs(doc.getObject(name).Shape.Volume-volume)<1e-5,(name,volume)
        assert doc.getObject(name).Shape.isValid()
    for obj in (doc.getObject('CutProfile'),doc.getObject('PlaneProfile')):
        if obj:obj.Visibility=False
    for obj in doc.Objects:
        if obj.Name.startswith('OffsetPlane'):obj.Visibility=False
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    history=Gui.getMainWindow().findChild(QtWidgets.QWidget,'FusionFlowHistory')
    assert history is not None and history.isVisible(),'History panel is missing'
    result={'pass':True,'version':App.Version()[:3],'volumes':expected,'file_bytes':Path(path).stat().st_size,
            'checks':['selected multi-body Cut','excluded body unchanged','preview Cancel','face Join',
                      'offset plane','attached sketch extrusion','section edges','FCStd save/reopen','timeline visible']}
except Exception:
    result={'pass':False,'error':traceback.format_exc()}
Path('/fusionflow-smoke.json').write_text(json.dumps(result),encoding='utf-8')
