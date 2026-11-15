import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-71,0))
r=w0.workplane(offset=-29/2).cylinder(29,12).union(w0.sketch().arc((-8,12),(0,-14),(8,12)).close().assemble().finalize().extrude(171))