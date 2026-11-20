import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,76,0))
r=w0.sketch().segment((-100,-69),(100,-69)).segment((100,69)).segment((-74.5,69)).segment((-100,69)).close().assemble().finalize().extrude(-152)