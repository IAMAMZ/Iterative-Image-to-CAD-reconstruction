import cadquery as cq
w0=cq.Workplane('YZ',origin=(43,0,0))
r=w0.workplane(offset=-143/2).cylinder(143,13).union(w0.workplane(offset=57/2).cylinder(57,9))