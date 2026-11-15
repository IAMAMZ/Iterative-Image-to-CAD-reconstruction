import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().circle(100).rect(37.5,37.5,mode='s').finalize().extrude(-12)