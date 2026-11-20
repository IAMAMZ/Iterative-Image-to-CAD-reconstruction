import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,12,0))
r=w0.workplane(offset=-26/2).moveTo(0,0).box(200,156.5,26).union(w0.sketch().segment((-17,-30),(20,-17)).segment((-1,7.5)).close().assemble().finalize().extrude(2))