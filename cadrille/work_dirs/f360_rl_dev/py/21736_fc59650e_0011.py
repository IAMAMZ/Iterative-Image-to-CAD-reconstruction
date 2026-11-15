import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().circle(100).circle(62.5,mode='s').finalize().extrude(-12)