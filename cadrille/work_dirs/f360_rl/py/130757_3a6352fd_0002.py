import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-29))
r=w0.sketch().segment((-60,-41),(59,-41)).arc((100,0),(60,41)).segment((-60,41)).arc((-100,0),(-60,-41)).assemble().finalize().extrude(11).union(w0.sketch().segment((-60,-32),(57,-32)).arc((89,3),(57,32)).segment((-60,32)).arc((-90,1),(-60,-32)).assemble().finalize().extrude(58))