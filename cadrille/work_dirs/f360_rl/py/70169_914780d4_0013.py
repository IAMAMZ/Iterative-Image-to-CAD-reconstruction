import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,37,0))
r=w0.sketch().segment((-100,-69),(-75,-98)).segment((75,-98)).segment((100,-69)).segment((100,69)).segment((75,98)).segment((-75,98)).segment((-79,91)).segment((-100,69)).close().assemble().finalize().extrude(-73)