import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().arc((-23,0),(16,-16),(1.5,23)).segment((-23,23)).close().assemble().finalize().extrude(-200)