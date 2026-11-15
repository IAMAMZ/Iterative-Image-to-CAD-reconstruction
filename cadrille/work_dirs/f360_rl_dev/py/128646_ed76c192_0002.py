import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,34))
r=w0.sketch().arc((-100,-2),(-6,-92),(85,-5)).segment((100,-2.5)).segment((100,2.5)).segment((85,5)).arc((-6,92),(-100,2)).close().assemble().push([(-8,0)]).circle(17,mode='s').finalize().extrude(-67)