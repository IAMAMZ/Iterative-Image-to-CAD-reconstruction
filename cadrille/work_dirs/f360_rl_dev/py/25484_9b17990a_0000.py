import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,99,0))
r=w0.sketch().arc((-91,-55),(13,-99),(92,-50.5)).segment((91.5,50.5)).segment((91.5,100)).segment((-91,100)).close().assemble().finalize().extrude(-197.5)