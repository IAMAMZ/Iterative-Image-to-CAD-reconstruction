import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,8,0))
r=w0.workplane(offset=-16/2).moveTo(0,0).box(200,119,16).union(w0.workplane(offset=-8/2).box(186.5,110.5,8))