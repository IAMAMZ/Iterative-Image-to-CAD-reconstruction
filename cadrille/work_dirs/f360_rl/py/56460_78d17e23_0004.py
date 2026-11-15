import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,14))
r=w0.sketch().circle(100).circle(82.5,mode='s').circle(21.5).circle(10,mode='s').finalize().extrude(-27.5)