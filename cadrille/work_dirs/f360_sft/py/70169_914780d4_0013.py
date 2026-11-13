import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,36,0))
r=w0.sketch().segment((-100,-66),(-74,-98)).segment((74,-98)).segment((100,-72)).segment((100,66)).segment((74,98)).segment((-74,98)).segment((-100,72)).close().assemble().finalize().extrude(-72)