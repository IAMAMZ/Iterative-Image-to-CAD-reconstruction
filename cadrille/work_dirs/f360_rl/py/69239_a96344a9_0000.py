import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-54,0))
w1=cq.Workplane('XY',origin=(0,0,91))
r=w0.workplane(offset=-12/2).moveTo(0,89.5).box(179.5,22,12).union(w0.workplane(offset=134/2).moveTo(0,-10).cylinder(134,5.5)).union(w1.sketch().segment((-100,-80),(-64,-80)).segment((-64,-53)).segment((55,-53)).segment((54.5,-80)).segment((90,-80)).segment((90,-7)).segment((-64,-6.5)).segment((-100,-6.5)).close().assemble().finalize().extrude(-181)).union(w1.workplane(offset=-139/2).moveTo(0,-29.5).box(79.5,39.5,139)).union(w1.workplane(offset=-129/2).moveTo(0.5,0.5).box(1.5,1.5,12))