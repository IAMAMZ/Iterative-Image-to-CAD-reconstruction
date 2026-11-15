import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,31,0))
r=w0.sketch().segment((-100,-64),(40,-64)).arc((100,0),(40,64)).segment((-10,64)).segment((-100,64)).close().assemble().reset().face(w0.sketch().segment((-95,-59),(40,-59)).arc((96,0),(40,59)).segment((-95,59)).close().assemble(),mode='s').finalize().extrude(-60)