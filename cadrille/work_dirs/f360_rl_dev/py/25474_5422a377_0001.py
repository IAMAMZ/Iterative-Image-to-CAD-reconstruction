import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-30,0))
r=w0.workplane(offset=20/2).cylinder(20,91.5).union(w0.sketch().arc((-98,-1),(-3,-100),(98,-29)).segment((86,-19.5)).segment((86.5,31.5)).segment((98,29)).arc((-3,100),(-98,1)).close().assemble().circle(59,mode='s').finalize().extrude(60))