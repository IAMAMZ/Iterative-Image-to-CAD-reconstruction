import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,16))
r=w0.sketch().circle(100).circle(50,mode='s').finalize().extrude(-33)