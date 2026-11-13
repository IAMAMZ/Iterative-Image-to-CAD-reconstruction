import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,14,0))
r=w0.sketch().push([(0,-86)]).circle(14).circle(7,mode='s').push([(0,86)]).circle(14).circle(7,mode='s').finalize().extrude(-28).union(w0.workplane(offset=-21/2).moveTo(0,-1).box(12,158,21))