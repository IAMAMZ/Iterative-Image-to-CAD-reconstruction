import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,45,0))
r=w0.workplane(offset=-89/2).moveTo(0,0).box(132.5,162.5,89).union(w0.workplane(offset=-82/2).box(133.5,200,82)).union(w0.workplane(offset=-80/2).moveTo(0,-38.5).box(129.5,123.5,80))