import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,17))
r=w0.sketch().arc((-100,-2),(-6,-94),(88,-6)).segment((100,-2)).segment((100,2.5)).segment((88,6)).arc((-6,94),(-100,2)).close().assemble().push([(-5,0)]).circle(2).finalize().extrude(-33.5)