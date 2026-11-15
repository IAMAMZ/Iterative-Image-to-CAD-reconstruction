import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-50,0))
r=w0.sketch().segment((-44,95),(42,16)).segment((-5,-93)).segment((-5,-100)).segment((44,-100)).segment((44,17)).segment((42,17)).segment((-39,100)).close().assemble().finalize().extrude(100)