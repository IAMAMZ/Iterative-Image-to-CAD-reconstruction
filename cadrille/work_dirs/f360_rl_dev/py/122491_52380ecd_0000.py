import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,40,0))
r=w0.workplane(offset=-80/2).moveTo(0,0).box(200,120,80).union(w0.workplane(offset=-49/2).box(170.5,10.5,49)).union(w0.workplane(offset=-19/2).box(196.5,113.5,19))