import cadquery as cq
w0=cq.Workplane('YZ',origin=(4,0,0))
r=w0.sketch().segment((-100,-33),(100,-33)).arc((77,-1),(39,33)).segment((-100,-30)).close().assemble().push([(35,5)]).circle(7,mode='s').finalize().extrude(-9)