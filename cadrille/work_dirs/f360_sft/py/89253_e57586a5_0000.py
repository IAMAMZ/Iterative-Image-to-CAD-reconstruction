import cadquery as cq
w0=cq.Workplane('YZ',origin=(-19,0,0))
r=w0.workplane(offset=-81/2).cylinder(81,40).union(w0.workplane(offset=39/2).cylinder(39,54)).union(w0.workplane(offset=119/2).cylinder(119,40))