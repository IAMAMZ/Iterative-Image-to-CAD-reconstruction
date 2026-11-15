import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,29))
r=w0.sketch().push([(-74,-67)]).circle(10.5).push([(-74,69)]).circle(10.5).push([(80,69)]).circle(9.5).push([(80,-67)]).circle(10).finalize().extrude(-78).union(w0.sketch().segment((-100,-83),(10,-83.5)).segment((100,-83)).segment((100,83)).segment((-10,83)).segment((-100,83)).close().assemble().finalize().extrude(20))