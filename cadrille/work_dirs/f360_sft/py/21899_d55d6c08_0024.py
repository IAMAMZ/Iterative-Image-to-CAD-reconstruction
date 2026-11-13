import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-20,0))
r=w0.workplane(offset=32/2).moveTo(-66,0).cylinder(32,14).union(w0.sketch().push([(-66,0)]).circle(34).circle(17,mode='s').push([(66,0)]).circle(34).circle(17,mode='s').finalize().extrude(40)).union(w0.workplane(offset=40/2).moveTo(1.5,0).box(61,28,40))