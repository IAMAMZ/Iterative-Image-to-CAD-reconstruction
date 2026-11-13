import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-37))
r=w0.sketch().circle(100).circle(86,mode='s').finalize().extrude(74)