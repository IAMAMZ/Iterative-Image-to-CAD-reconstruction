import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,75,0))
r=w0.workplane(offset=-175/2).moveTo(0,0).cylinder(175,7.5).union(w0.workplane(offset=-169/2).moveTo(0,0).cylinder(169,7.5)).union(w0.workplane(offset=25/2).cylinder(25,5.5)).union(w0.workplane(offset=25/2).cylinder(25,5))