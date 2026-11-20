import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-46))
r=w0.workplane(offset=-54/2).cylinder(54,29).union(w0.sketch().circle(17.5).circle(7,mode='s').finalize().extrude(146))