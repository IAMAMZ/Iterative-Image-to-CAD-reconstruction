import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-1,0))
r=w0.sketch().segment((-100,-3),(100,-3)).segment((100,3)).segment((92,3)).segment((92,0)).segment((88,0)).segment((88,3)).segment((-98,3)).arc((-99,0),(-100,-3)).assemble().finalize().extrude(3)