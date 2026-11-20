import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,4))
r=w0.sketch().segment((-91,-12),(91,-12)).arc((100,3),(91,12)).segment((-91,12)).arc((-100,1),(-91,-12)).assemble().push([(-88,0)]).circle(6,mode='s').push([(88,0)]).circle(6,mode='s').finalize().extrude(-7)