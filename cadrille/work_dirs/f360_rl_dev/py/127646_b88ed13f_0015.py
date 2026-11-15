import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-43,0))
r=w0.workplane(offset=-57/2).cylinder(57,17).union(w0.workplane(offset=-35.5/2).box(142.5,143.5,35.5)).union(w0.workplane(offset=143/2).moveTo(0,0).box(35.5,142.5,143)).union(w0.workplane(offset=-19/2).box(1.5,1.5,1))