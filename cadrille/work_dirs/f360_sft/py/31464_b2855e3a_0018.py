import cadquery as cq
w0=cq.Workplane('YZ',origin=(-89,0,0))
r=w0.sketch().circle(100).circle(89,mode='s').finalize().extrude(178)