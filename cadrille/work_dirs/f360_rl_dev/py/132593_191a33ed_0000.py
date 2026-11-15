import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,15,0))
r=w0.sketch().arc((-100,-73),(-89,-93),(-69,-100)).segment((69,-100)).segment((89,-97)).segment((100,-73)).segment((100,73.5)).arc((93,89),(79,100)).segment((-69.5,100)).segment((-89,100)).segment((-100,73.5)).close().assemble().finalize().extrude(-30)