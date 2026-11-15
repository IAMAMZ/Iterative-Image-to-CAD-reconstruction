import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,26.5,0))
r=w0.workplane(offset=-53/2).moveTo(0,0).box(200,30,53).union(w0.workplane(offset=-9/2).box(196.5,2.5,9))