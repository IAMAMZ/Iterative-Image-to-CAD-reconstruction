import cadquery as cq
w0=cq.Workplane('YZ',origin=(-47,0,0))
r=w0.sketch().circle(100).circle(89,mode='s').finalize().extrude(30.5).union(w0.sketch().circle(100).circle(86,mode='s').finalize().extrude(94))