import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.sketch().arc((-16,-100),(13,-57),(16,-10)).segment((16.5,100)).segment((0,100)).segment((0,10)).segment((-10,1)).segment((-16,-4)).close().assemble().finalize().extrude(-50)