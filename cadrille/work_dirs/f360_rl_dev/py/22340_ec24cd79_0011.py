import cadquery as cq
w0=cq.Workplane('YZ',origin=(53,0,0))
r=w0.workplane(offset=-153/2).cylinder(153,34.5).union(w0.workplane(offset=47/2).moveTo(0,0).box(44.5,44.5,47))