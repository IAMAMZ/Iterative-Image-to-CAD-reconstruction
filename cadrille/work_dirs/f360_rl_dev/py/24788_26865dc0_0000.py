import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,15,0))
r=w0.sketch().rect(114,200).reset().face(w0.sketch().segment((-13,-31),(13,-39)).segment((15,70)).segment((-12.5,71)).segment((-15,57.5)).close().assemble(),mode='s').finalize().extrude(-29)