import cadquery as cq
w0=cq.Workplane('YZ',origin=(32,0,0))
r=w0.workplane(offset=-63/2).cylinder(63,7.5).union(w0.sketch().circle(100).finalize().extrude(-20)).union(w0.sketch().circle(54.5).finalize().extrude(-13))