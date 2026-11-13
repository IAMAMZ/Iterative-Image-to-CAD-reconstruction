import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,23))
r=w0.sketch().circle(100).circle(66.5,mode='s').finalize().extrude(-46.5)