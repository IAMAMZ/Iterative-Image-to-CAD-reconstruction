import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,50,0))
r=w0.workplane(offset=-100/2).moveTo(0,0).box(200,100,100).union(w0.workplane(offset=-49/2).box(170.5,89.5,49))