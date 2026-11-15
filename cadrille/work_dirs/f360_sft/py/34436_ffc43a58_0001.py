import cadquery as cq
w0=cq.Workplane('YZ',origin=(31,0,0))
r=w0.sketch().segment((-100,-19),(-90,-1)).segment((-87,-3)).segment((-87,-31)).segment((100,-31)).segment((100,31)).segment((-87,31)).segment((-87,1)).segment((-100,19)).close().assemble().push([(74,12)]).circle(13,mode='s').finalize().extrude(-62)