import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-31,0))
r=w0.sketch().rect(200,175).reset().face(w0.sketch().segment((-60,-46),(60,-46)).segment((60,46)).segment((40.5,46)).segment((-60,45)).close().assemble(),mode='s').finalize().extrude(-38).union(w0.workplane(offset=100/2).moveTo(0,0).box(150,125,100)).union(w0.workplane(offset=-2/2).box(1.5,1.5,1))