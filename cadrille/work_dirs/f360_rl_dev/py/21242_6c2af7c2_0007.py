import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-1))
r=w0.sketch().segment((-7,-86),(0,-100)).segment((7,-86)).segment((7.5,86)).segment((0,100)).segment((-7,86)).close().assemble().finalize().extrude(3.5)