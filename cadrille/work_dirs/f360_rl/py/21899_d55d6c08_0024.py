import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,21,0))
w1=cq.Workplane('ZX',origin=(0,14,0))
r=w0.sketch().push([(-66,0)]).circle(34).circle(16.5,mode='s').push([(66,0)]).circle(34).circle(16.5,mode='s').finalize().extrude(-41).union(w1.workplane(offset=-27/2).moveTo(0,0).box(50.5,32.5,27)).union(w1.workplane(offset=-11/2).moveTo(97,0.5).box(2,1.5,6))