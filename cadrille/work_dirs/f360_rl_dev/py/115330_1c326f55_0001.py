import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().segment((-87,-34),(86.5,-34)).segment((87,-14)).arc((100,0),(87,14)).segment((87,34)).segment((-87,34)).segment((-87,12)).arc((-100,0),(-87,-12)).close().assemble().push([(-88,0)]).circle(6.5,mode='s').push([(88,0)]).circle(6.5,mode='s').finalize().extrude(-16.5)