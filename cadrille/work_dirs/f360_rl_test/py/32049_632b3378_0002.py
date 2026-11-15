import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,28.5,0))
r=w0.workplane(offset=-56.5/2).moveTo(0,0).box(133.5,200,56).union(w0.workplane(offset=-10/2).box(129.5,186.5,10))