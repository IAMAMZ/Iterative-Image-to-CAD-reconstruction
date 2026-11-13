import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-4))
r=w0.sketch().arc((-88,-11),(0,-88),(88,-11)).segment((97,-11)).arc((99,-3),(100,5)).segment((88,5)).arc((0,88),(-88,5)).arc((-100,-2),(-88,-11)).assemble().push([(0,-1)]).circle(44,mode='s').finalize().extrude(7)