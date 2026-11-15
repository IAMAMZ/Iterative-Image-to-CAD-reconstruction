import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,85,0))
r=w0.workplane(offset=-185/2).cylinder(185,8).union(w0.workplane(offset=15/2).cylinder(15,4)).union(w0.workplane(offset=15/2).box(2.5,5.5,15))