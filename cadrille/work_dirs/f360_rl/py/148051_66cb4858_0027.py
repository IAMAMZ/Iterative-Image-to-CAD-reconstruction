import cadquery as cq
w0=cq.Workplane('YZ',origin=(5,0,0))
r=w0.sketch().segment((-100,-33),(100,-32.5)).segment((100,-30)).segment((33,33)).segment((-100,-27)).close().assemble().push([(34,3)]).circle(7,mode='s').finalize().extrude(-9)