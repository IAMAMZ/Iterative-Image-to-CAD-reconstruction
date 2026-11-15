import cadquery as cq
w0=cq.Workplane('YZ',origin=(95,0,0))
w1=cq.Workplane('ZX',origin=(0,20,0))
r=w0.sketch().segment((-12,2),(12,3)).segment((12,21)).segment((-12,16)).close().assemble().finalize().extrude(-195.5).union(w1.sketch().segment((-22,87),(2,87)).segment((22,87)).segment((22,94.5)).segment((12.5,100)).segment((-2,100)).segment((-22,93)).close().assemble().finalize().extrude(-39.5)).union(w1.workplane(offset=-19/2).moveTo(17.5,97.5).box(1.5,1.5,1))