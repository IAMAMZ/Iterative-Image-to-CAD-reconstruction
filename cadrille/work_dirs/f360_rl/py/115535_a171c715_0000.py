import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,7,0))
r=w0.sketch().segment((-100,-2),(-71,-2)).segment((-72,-17)).segment((-57,-17)).segment((-60,-2)).segment((100,-2.5)).segment((100,17)).segment((-100,17)).close().assemble().finalize().extrude(-13)