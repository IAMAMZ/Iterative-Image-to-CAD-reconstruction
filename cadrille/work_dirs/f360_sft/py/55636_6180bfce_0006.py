import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().segment((-98,-99),(-86,-100)).segment((1,86)).segment((88,-100)).segment((98,-100)).segment((2,92)).segment((2,100)).segment((-2,100)).segment((-2,92)).segment((-1,92)).close().assemble().reset().face(w0.sketch().segment((35,15),(40,15)).segment((40,21)).arc((38,18),(35,15)).assemble(),mode='s').finalize().extrude(-14)