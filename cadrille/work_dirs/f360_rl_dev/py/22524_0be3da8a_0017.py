import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,12))
r=w0.sketch().segment((-83,-57),(83,-57)).arc((100,3),(83,57)).segment((-83,57)).arc((-100,2),(-83,-57)).assemble().push([(-56,0)]).circle(21.5,mode='s').push([(0,0)]).circle(21.5,mode='s').push([(56,0)]).circle(21.5,mode='s').finalize().extrude(-22)