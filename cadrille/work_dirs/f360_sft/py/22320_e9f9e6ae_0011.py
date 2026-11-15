import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-2))
r=w0.sketch().segment((-100,7),(-64,0)).arc((-64,-13),(-56,-23)).segment((-47,3)).segment((100,3)).segment((100,11)).segment((-46,11)).segment((-45,17)).arc((-52,18),(-59,17)).segment((-97,17)).close().assemble().finalize().extrude(4)