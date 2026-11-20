import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-12,0))
r=w0.sketch().circle(100).finalize().extrude(20).union(w0.sketch().segment((-60,30),(-17,-11)).segment((6,0)).segment((6,11)).segment((-19,57.5)).close().assemble().finalize().extrude(23.5)).union(w0.workplane(offset=23/2).box(1.5,1.5,23))