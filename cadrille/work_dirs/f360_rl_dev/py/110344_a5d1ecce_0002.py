import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().circle(100).circle(52.5,mode='s').finalize().extrude(-9.5)