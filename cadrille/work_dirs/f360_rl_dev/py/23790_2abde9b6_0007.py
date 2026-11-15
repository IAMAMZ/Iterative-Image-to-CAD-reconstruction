import cadquery as cq
w0=cq.Workplane('YZ',origin=(10,0,0))
r=w0.workplane(offset=-110/2).cylinder(110,44.5).union(w0.sketch().circle(78).circle(35.5,mode='s').finalize().extrude(90))