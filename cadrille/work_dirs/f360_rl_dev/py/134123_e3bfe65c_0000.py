import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,72,0))
r=w0.sketch().segment((-20,-90),(-14,-90)).segment((-14,-100)).segment((15,-100)).segment((15,-90)).segment((20,-90)).segment((20,100)).segment((-20,100)).close().assemble().finalize().extrude(-143)