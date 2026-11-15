import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
w1=cq.Workplane('ZX',origin=(0,-20,0))
r=w0.sketch().segment((-19,42),(87,-100)).segment((92,-89.5)).segment((-15,47)).close().assemble().finalize().extrude(-50.5).union(w0.sketch().segment((85,79),(93.5,79)).segment((94.5,100)).segment((85.5,100)).close().assemble().finalize().extrude(-17.5)).union(w0.sketch().segment((-93,-2),(-49,-31)).segment((0,0.5)).segment((-89,8.5)).close().assemble().push([(87.5,-92.5)]).rect(7.5,13.5).finalize().extrude(10)).union(w1.workplane(offset=-10/2).moveTo(87.5,-92.5).box(5,9.5,9))