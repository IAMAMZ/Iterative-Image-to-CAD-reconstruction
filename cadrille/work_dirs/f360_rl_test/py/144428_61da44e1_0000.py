import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-30))
r=w0.sketch().segment((-69,-30),(75,-30)).arc((100,0),(75,30)).segment((-69,30)).arc((-100,0),(-69,-30)).assemble().finalize().extrude(-20).union(w0.sketch().push([(-42,0)]).circle(20).push([(40,0)]).circle(20).finalize().extrude(80))