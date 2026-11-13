import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,71,0))
r=w0.workplane(offset=-171/2).cylinder(171,5).union(w0.workplane(offset=-164/2).cylinder(164,8)).union(w0.workplane(offset=29/2).cylinder(29,5))