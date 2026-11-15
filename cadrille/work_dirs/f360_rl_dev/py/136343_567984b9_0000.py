import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-0,0))
r=w0.sketch().segment((-52,-100),(-40,-100)).segment((-40,-92)).segment((40,-92)).segment((40,-100)).segment((52,-100)).segment((52,100)).segment((40,100)).segment((40,92)).segment((-40,92)).segment((-40,100)).segment((-52,100)).close().assemble().finalize().extrude(1.5)