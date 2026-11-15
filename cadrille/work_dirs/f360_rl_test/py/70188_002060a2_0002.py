import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,7))
r=w0.sketch().arc((-33,67),(-85,-35),(0,-100)).arc((85,-35),(36,67)).segment((17,93)).segment((12.5,100)).segment((-22,100)).close().assemble().push([(0,-13)]).circle(3,mode='s').finalize().extrude(-14)