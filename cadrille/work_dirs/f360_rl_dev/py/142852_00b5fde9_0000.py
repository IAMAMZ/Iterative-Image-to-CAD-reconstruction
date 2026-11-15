import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,5))
r=w0.workplane(offset=-10/2).moveTo(0,0).box(200,20,10).union(w0.sketch().segment((-30,-12),(20,-8)).segment((-6,12)).close().assemble().finalize().extrude(-2))