import cadquery as cq
w0=cq.Workplane('YZ',origin=(-28,0,0))
r=w0.sketch().circle(100).circle(12,mode='s').finalize().extrude(15).union(w0.sketch().circle(25).circle(8,mode='s').finalize().extrude(55))