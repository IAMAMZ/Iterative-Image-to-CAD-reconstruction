import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-48,0))
r=w0.workplane(offset=-52/2).cylinder(52,33.5).union(w0.workplane(offset=148/2).cylinder(148,13.5)).union(w0.workplane(offset=-9/2).box(1.5,1.5,1))