import cadquery as cq
w0=cq.Workplane('YZ',origin=(25,0,0))
r=w0.sketch().circle(94.5).circle(89,mode='s').finalize().extrude(-50).union(w0.workplane(offset=-31/2).cylinder(31,93)).union(w0.sketch().circle(100).finalize().extrude(-24))