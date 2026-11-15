import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,11))
r=w0.sketch().segment((-39,-100),(-17,-100)).arc((0,-81),(17,-100)).segment((39,-100)).segment((39,-77)).segment((15,-77)).segment((14.5,68)).arc((0,100),(-15,69)).segment((-15,66)).segment((-15,59)).segment((-15,-77)).segment((-39,-77)).close().assemble().push([(0,81)]).circle(6.5,mode='s').finalize().extrude(-20)