import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,1))
r=w0.sketch().segment((-100,18),(-65,-20)).segment((-53,-13)).segment((-26,-18)).segment((0,3)).segment((41.5,11)).segment((100,15)).segment((97,18)).segment((-26.5,17)).close().assemble().finalize().extrude(-2)