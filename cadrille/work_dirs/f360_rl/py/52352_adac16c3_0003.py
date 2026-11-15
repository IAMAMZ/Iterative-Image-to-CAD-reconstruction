import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,13,0))
r=w0.sketch().segment((-100,-94),(-89,-94)).segment((-89,83)).segment((89,83)).segment((89,-94)).segment((100,-94)).segment((100,94)).segment((-100,94)).close().assemble().finalize().extrude(-26).union(w0.workplane(offset=-5.5/2).moveTo(0,0).box(200,187.5,5.5)).union(w0.workplane(offset=-4/2).box(17.5,1.5,4))