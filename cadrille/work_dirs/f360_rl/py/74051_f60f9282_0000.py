import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,87,0))
w1=cq.Workplane('ZX',origin=(0,19,0))
r=w0.sketch().segment((-100,-100),(100,-100)).segment((100,-20)).segment((93,-20)).segment((93,-94)).segment((-93,-94)).segment((-94,94)).segment((-40,94)).segment((-40,100)).segment((-100,100)).close().assemble().finalize().extrude(-175).union(w0.workplane(offset=-39.5/2).moveTo(39.5,-49.5).box(1.5,1.5,39.5)).union(w1.workplane(offset=-22/2).moveTo(0,0).box(19.5,1.5,22)).union(w1.workplane(offset=-19/2).moveTo(97.5,-4.5).box(1.5,1.5,1))