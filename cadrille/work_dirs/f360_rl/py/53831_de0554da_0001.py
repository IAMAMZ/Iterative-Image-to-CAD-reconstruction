import cadquery as cq
w0=cq.Workplane('YZ',origin=(62,0,0))
r=w0.workplane(offset=-124/2).cylinder(124,12.5).union(w0.sketch().circle(100).finalize().extrude(-25)).union(w0.workplane(offset=-13/2).moveTo(0,-21).box(190.5,8.5,13))