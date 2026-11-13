import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-3,0))
r=w0.sketch().segment((-100,-68),(100,-98)).segment((100,-62)).segment((-30,-39)).segment((6,-1)).segment((-29,37)).segment((100,68)).segment((98,98)).segment((-100,67)).segment((-100,35)).segment((-84,22)).segment((-69,-10)).segment((-100,-32)).close().assemble().finalize().extrude(7)