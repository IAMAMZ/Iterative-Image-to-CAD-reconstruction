import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-78,0))
r=w0.workplane(offset=-22/2).box(22,7,22).union(w0.workplane(offset=178/2).cylinder(178,6.5)).union(w0.workplane(offset=178/2).box(1.5,1.5,2))