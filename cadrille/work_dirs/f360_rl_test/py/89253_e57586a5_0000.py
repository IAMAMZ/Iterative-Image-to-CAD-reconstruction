import cadquery as cq
w0=cq.Workplane('YZ',origin=(20,0,0))
r=w0.workplane(offset=-120/2).cylinder(120,40).union(w0.workplane(offset=-39/2).cylinder(39,54)).union(w0.workplane(offset=80/2).cylinder(80,40)).union(w0.workplane(offset=80/2).cylinder(80,6))