import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,31))
r=w0.sketch().arc((-100,-2),(-13,-89),(79,-8)).segment((100,-4)).segment((100,5)).segment((78,8)).arc((-12,89),(-100,2)).close().assemble().push([(-12,0)]).circle(31.5,mode='s').finalize().extrude(-60)