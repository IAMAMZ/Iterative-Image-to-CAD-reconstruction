import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,0))
w1=cq.Workplane('ZX',origin=(0,-50,0))
r=w0.sketch().segment((-100,-90),(100,-90)).segment((100,-49)).segment((-19,0)).segment((-59,90)).segment((-100,90)).close().assemble().finalize().extrude(-70).union(w0.workplane(offset=70/2).moveTo(-80,0.5).box(40,180.5,70)).union(w1.sketch().segment((-70,-100),(69,-100)).segment((70,11)).arc((49,62),(-1,100)).segment((-70,100)).close().assemble().finalize().extrude(-40)).union(w1.workplane(offset=140/2).moveTo(60.5,-89.5).box(17.5,11.5,140))