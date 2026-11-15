import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,6))
r=w0.sketch().segment((-62,-100),(62.5,-100)).segment((62.5,100)).segment((-13.5,100)).segment((-14,86)).arc((0,0),(-17,-63)).segment((-23,-71)).segment((-26,-81)).close().assemble().finalize().extrude(-10.5)