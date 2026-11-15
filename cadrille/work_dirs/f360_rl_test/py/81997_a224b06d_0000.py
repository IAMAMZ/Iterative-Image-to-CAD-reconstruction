import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,24,0))
r=w0.sketch().segment((-25,60),(0,-100)).segment((25,60)).segment((16,62)).segment((14,83)).segment((10,98)).segment((7,100)).segment((-10,100)).segment((-14,89)).segment((-16,64.5)).close().assemble().finalize().extrude(-47.5)