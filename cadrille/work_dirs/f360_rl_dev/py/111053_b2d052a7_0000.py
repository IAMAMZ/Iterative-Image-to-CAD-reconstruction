import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,75,0))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().arc((-100,-49),(-89,-69),(-69,-80)).segment((-1,-80)).segment((-1,-49)).segment((-39,-49)).segment((-57,-31)).segment((-57,80)).segment((-100,80)).close().assemble().push([(87,-62)]).rect(26,35).finalize().extrude(-150).union(w1.workplane(offset=59/2).moveTo(-69.5,49.5).box(19.5,50.5,59)).union(w1.workplane(offset=59/2).moveTo(76.5,70.5).box(2.5,1.5,1))