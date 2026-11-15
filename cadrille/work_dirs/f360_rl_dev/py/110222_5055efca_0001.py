import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,10))
r=w0.sketch().circle(100).circle(25,mode='s').finalize().extrude(-60).union(w0.workplane(offset=40/2).moveTo(63,0).cylinder(40,12))