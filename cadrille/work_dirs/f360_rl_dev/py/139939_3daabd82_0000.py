import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,16))
r=w0.sketch().circle(100).circle(73.5,mode='s').circle(35).circle(20.5,mode='s').finalize().extrude(-33.5)