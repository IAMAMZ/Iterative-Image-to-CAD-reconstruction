import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,21))
r=w0.sketch().arc((-100,-2),(-22,-81),(61,-10)).segment((83,-13)).arc((100,2),(83,11)).segment((61,11)).arc((-22,81),(-100,2)).close().assemble().push([(-19,0)]).circle(18,mode='s').finalize().extrude(-42)