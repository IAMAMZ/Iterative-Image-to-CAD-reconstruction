import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-25,0))
r=w0.sketch().segment((-85,38),(-2,-1)).segment((-2,1)).segment((1,1)).segment((-83,42)).close().assemble().finalize().extrude(11).union(w0.sketch().circle(100).circle(90,mode='s').finalize().extrude(50))