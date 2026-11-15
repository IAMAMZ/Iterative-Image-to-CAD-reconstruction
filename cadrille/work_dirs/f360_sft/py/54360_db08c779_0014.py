import cadquery as cq
w0=cq.Workplane('YZ',origin=(-35,0,0))
r=w0.sketch().circle(100).circle(70,mode='s').finalize().extrude(-19).union(w0.sketch().circle(78).circle(54,mode='s').finalize().extrude(85))