import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.sketch().circle(100).circle(8.5).rect(8.5,7.5).finalize().extrude(-38).union(w0.workplane(offset=28/2).cylinder(28,28)).union(w0.workplane(offset=-11/2).box(1.5,1.5,6.5))