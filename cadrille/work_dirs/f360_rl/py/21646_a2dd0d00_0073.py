import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-62,-16),(19,-40)).segment((62,-40)).segment((62.5,40)).segment((19,40)).segment((-62,17)).close().assemble().finalize().extrude(-200)