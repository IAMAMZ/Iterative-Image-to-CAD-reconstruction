import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,6,0))
r=w0.sketch().segment((-100,-40),(-80,-67)).segment((-40,-100)).segment((40,-100)).segment((89,-50)).segment((100,-30.5)).segment((100,40)).segment((40,100)).segment((-40,100)).segment((-89,50)).segment((-100,30)).close().assemble().circle(96,mode='s').circle(61).finalize().extrude(-12).union(w0.workplane(offset=-6/2).cylinder(6,36.5))