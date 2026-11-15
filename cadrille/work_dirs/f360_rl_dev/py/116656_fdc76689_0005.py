import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().segment((-87,-14),(87,-14.5)).arc((100,0),(87,14)).segment((-87,14)).arc((-100,1),(-87,-14)).assemble().push([(-86,0)]).circle(8.5,mode='s').push([(86,0)]).circle(8.5,mode='s').finalize().extrude(-12)