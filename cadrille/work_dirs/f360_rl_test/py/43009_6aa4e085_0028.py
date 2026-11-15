import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,12))
r=w0.sketch().circle(100).circle(61.5,mode='s').finalize().extrude(-23)