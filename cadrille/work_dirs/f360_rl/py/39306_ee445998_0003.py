import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-74,0))
r=w0.workplane(offset=-26/2).cylinder(26,100).union(w0.workplane(offset=174/2).cylinder(174,66.5)).union(w0.workplane(offset=8/2).box(1.5,1.5,1))