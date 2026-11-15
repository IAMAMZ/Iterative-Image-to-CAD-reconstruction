import cadquery as cq
w0=cq.Workplane('YZ',origin=(16,0,0))
r=w0.sketch().circle(100).circle(80,mode='s').circle(17).circle(7.5,mode='s').finalize().extrude(-33)