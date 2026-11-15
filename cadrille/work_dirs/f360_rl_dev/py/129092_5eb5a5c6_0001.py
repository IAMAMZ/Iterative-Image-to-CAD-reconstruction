import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,16))
r=w0.sketch().arc((-100,-2),(-1,-95),(91,-2)).segment((100,0)).segment((91,11)).arc((6,95),(-100,2)).close().assemble().push([(-4,0)]).circle(11.5,mode='s').finalize().extrude(-31)