import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,44,0))
r=w0.workplane(offset=-144/2).cylinder(144,43).union(w0.sketch().circle(71).push([(-27,0)]).rect(25.5,23.5,mode='s').push([(0,0)]).rect(17.5,79.5,mode='s').push([(27,0)]).rect(24.5,23.5,mode='s').finalize().extrude(56))