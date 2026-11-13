import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.workplane(offset=-200/2).moveTo(0,0).box(76.5,29.5,200).union(w0.workplane(offset=-4/2).moveTo(0,0).box(135.5,61,4)).union(w0.workplane(offset=-4/2).moveTo(0,0).box(134.5,60.5,4))