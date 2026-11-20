import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-16,0))
r=w0.sketch().segment((-85,-1),(71,-100)).segment((85,100)).close().assemble().finalize().extrude(7).union(w0.sketch().segment((-60,0),(74,-81)).segment((80,81)).close().assemble().finalize().extrude(31))