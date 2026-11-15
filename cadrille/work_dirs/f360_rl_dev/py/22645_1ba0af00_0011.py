import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,79,0))
w1=cq.Workplane('ZX',origin=(0,-35,0))
r=w0.workplane(offset=-153/2).cylinder(153,62).union(w0.workplane(offset=-89/2).cylinder(89,61.5)).union(w0.workplane(offset=-8/2).cylinder(8,100)).union(w1.sketch().segment((-75,-1),(-74,-1)).arc((0,-74),(74,-1)).segment((76,1)).segment((75,10.5)).arc((0,74),(-74,10)).close().assemble().finalize().extrude(-43.5)).union(w1.workplane(offset=11/2).box(10.5,1.5,6))