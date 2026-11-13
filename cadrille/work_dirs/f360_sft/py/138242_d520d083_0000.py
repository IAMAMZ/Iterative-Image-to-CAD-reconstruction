import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-86,-47),(-80,-47)).segment((-80,42)).segment((86,42)).segment((86,47)).segment((-86,47)).close().assemble().finalize().extrude(200)