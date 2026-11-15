import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-59))
r=w0.workplane(offset=-41/2).cylinder(41,24).union(w0.workplane(offset=-18/2).cylinder(18,26)).union(w0.workplane(offset=15/2).box(1.5,1.5,1.5)).union(w0.workplane(offset=159/2).cylinder(159,9)).union(w0.workplane(offset=1/2).box(1.5,1.5,1))