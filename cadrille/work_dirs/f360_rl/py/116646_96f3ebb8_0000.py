import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,35,0))
w1=cq.Workplane('XY',origin=(0,0,86))
r=w0.sketch().segment((-86,-100),(0,-100)).segment((0,-54)).segment((86,-43)).segment((86,43)).segment((14,43)).segment((0,55)).segment((0,100)).segment((-86,100)).close().assemble().finalize().extrude(-69).union(w0.workplane(offset=-19/2).moveTo(82,-9.5).box(8,1.5,6.5)).union(w1.workplane(offset=-79/2).moveTo(-67,0.5).cylinder(79,9.5)).union(w1.workplane(offset=-19/2).moveTo(9.5,0.5).box(1.5,1.5,1))