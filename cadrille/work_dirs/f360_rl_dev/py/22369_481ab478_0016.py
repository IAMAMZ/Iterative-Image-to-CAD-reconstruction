import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,100,0))
w1=cq.Workplane('XY',origin=(0,0,1))
r=w0.sketch().segment((-60,-100),(10,-100)).segment((60,-61)).segment((60,-21)).segment((25,-20)).segment((24,16)).segment((60,16)).segment((60,61)).segment((0,100)).segment((-60,100)).close().assemble().finalize().extrude(-200).union(w1.workplane(offset=-6/2).moveTo(97.5,97.5).box(1.5,1.5,2))