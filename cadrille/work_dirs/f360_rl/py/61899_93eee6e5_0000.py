import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-40))
w1=cq.Workplane('XY',origin=(0,0,-29))
r=w0.sketch().segment((-79,-1),(-49,-37)).segment((100,-37)).segment((100,-10)).segment((-19,-7)).segment((-62,37)).segment((-79,31.5)).close().assemble().finalize().extrude(69.5).union(w0.sketch().segment((-100,18),(-92,8)).segment((-63,6)).segment((-77,31)).segment((-94,27)).close().assemble().finalize().extrude(80)).union(w1.workplane(offset=6/2).moveTo(97.5,-0.5).box(3.5,1,6))