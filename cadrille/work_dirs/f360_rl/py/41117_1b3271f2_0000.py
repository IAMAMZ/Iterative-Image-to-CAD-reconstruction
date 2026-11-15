import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-29))
w1=cq.Workplane('XY',origin=(0,0,29))
r=w0.workplane(offset=8/2).moveTo(0,0).box(196.5,33.5,8).union(w1.sketch().segment((-100,-7),(99,-7.5)).segment((100,14)).segment((-74.5,14.5)).segment((-100,14)).close().assemble().finalize().extrude(-31)).union(w1.workplane(offset=-8/2).moveTo(97.5,-13.5).box(1.5,1.5,7))