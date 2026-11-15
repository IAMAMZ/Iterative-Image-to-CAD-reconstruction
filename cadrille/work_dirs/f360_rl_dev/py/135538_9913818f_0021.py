import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().segment((-100,-61),(-62,-100)).segment((100,-100)).segment((100,-21)).segment((-22,100)).segment((-100,100)).close().assemble().finalize().extrude(-13)