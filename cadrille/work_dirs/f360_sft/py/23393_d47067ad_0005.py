import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-12))
r=w0.sketch().segment((-1,-100),(1,-100)).segment((1,-99)).arc((0,-99),(-1,-98)).close().assemble().reset().face(w0.sketch().arc((-1,99),(0,98),(1,97)).segment((1,100)).segment((-1,100)).close().assemble()).finalize().extrude(12).union(w0.workplane(offset=24/2).box(2,200,24))