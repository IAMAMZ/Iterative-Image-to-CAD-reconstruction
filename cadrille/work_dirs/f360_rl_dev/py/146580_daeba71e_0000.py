import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,14,0))
r=w0.sketch().arc((-100,-2),(-95,-13),(-93,-31)).arc((7,-98),(100,-4)).arc((7,98),(-100,2)).close().assemble().finalize().extrude(-29)