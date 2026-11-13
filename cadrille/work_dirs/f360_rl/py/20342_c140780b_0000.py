import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,27,0))
r=w0.workplane(offset=-54/2).moveTo(0,-0).box(200,50,54).union(w0.workplane(offset=-8/2).box(196.5,19.5,8))