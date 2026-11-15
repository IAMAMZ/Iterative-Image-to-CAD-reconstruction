import cadquery as cq
w0=cq.Workplane('YZ',origin=(-1,0,0))
r=w0.sketch().circle(100).circle(83,mode='s').finalize().extrude(2)