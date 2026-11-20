import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2,0))
r=w0.sketch().segment((-20,-16),(-14,-19)).segment((-10,-92)).arc((0,-100),(10,-92)).segment((14,-18)).segment((20,-8)).segment((20,91)).segment((-12,100)).segment((-20,88)).close().assemble().finalize().extrude(4)