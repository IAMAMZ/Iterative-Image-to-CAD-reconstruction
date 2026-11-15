import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,13))
r=w0.sketch().circle(100).circle(34,mode='s').finalize().extrude(-25)