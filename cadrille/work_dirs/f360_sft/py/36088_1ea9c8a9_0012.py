import cadquery as cq
w0=cq.Workplane('YZ',origin=(-21,0,0))
r=w0.sketch().circle(100).circle(71,mode='s').finalize().extrude(13).union(w0.sketch().circle(45).circle(35,mode='s').finalize().extrude(42))