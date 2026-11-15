import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6.5,0))
r=w0.workplane(offset=-12/2).moveTo(0,0).box(200,122,12).union(w0.workplane(offset=-6/2).box(186.5,110.5,6))