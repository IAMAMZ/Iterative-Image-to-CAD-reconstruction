import cadquery as cq
w0=cq.Workplane('YZ',origin=(85,0,0))
r=w0.sketch().circle(8).circle(4,mode='s').finalize().extrude(-185).union(w0.workplane(offset=15/2).cylinder(15,3))