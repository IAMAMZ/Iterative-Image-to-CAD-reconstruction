import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-20,0))
r=w0.sketch().segment((-21,-14),(54,-100)).segment((54,100)).arc((20,53),(-13,7)).arc((-16,-5),(-21,-14)).assemble().finalize().extrude(10).union(w0.workplane(offset=40/2).moveTo(-35,0).cylinder(40,20))