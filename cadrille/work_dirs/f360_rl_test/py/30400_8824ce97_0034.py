import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-5,4),(4,4)).segment((4,-4.5)).segment((5,-5)).segment((5.5,-4)).segment((5.5,5.5)).segment((2.5,6)).segment((-5,6)).close().assemble().finalize().extrude(-200)