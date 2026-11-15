import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-25,0))
r=w0.sketch().segment((-90,11),(-6,1)).segment((-80,49.5)).close().assemble().finalize().extrude(6.5).union(w0.sketch().circle(100).circle(90,mode='s').finalize().extrude(50))