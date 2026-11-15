import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-30))
r=w0.sketch().segment((-65,-31),(71,-31)).segment((71,-30)).arc((100,0),(71,30)).segment((71,31)).segment((-65,31)).segment((-65,30)).arc((-100,0),(-65,-30)).close().assemble().finalize().extrude(-20).union(w0.sketch().push([(-41,-1)]).circle(20).push([(40,-1)]).circle(20).finalize().extrude(80))