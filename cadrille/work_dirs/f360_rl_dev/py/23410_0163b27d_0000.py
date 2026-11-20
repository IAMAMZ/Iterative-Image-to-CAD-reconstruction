import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,23))
r=w0.sketch().circle(100).circle(73,mode='s').finalize().extrude(-45.5)