import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,71))
r=w0.sketch().arc((-10,82),(0,-100),(10,82)).segment((7,100)).segment((-7,100)).close().assemble().push([(0,-9)]).circle(62,mode='s').finalize().extrude(-141)