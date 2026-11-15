import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
r=w0.sketch().circle(100).reset().face(w0.sketch().segment((-69,46),(45,-74)).segment((69,-46)).segment((-45,74)).close().assemble()).finalize().extrude(-20).union(w0.workplane(offset=-10/2).cylinder(10,100))