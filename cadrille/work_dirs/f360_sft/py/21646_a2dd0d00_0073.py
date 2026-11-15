import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
r=w0.sketch().segment((-62,-16),(18,-40)).segment((62,-40)).segment((62,40)).segment((22,40)).segment((22,37)).segment((-59,17)).segment((-62,17)).close().assemble().finalize().extrude(-200)