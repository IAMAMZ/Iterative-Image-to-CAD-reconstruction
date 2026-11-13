import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,29))
w1=cq.Workplane('ZX',origin=(0,41,0))
r=w0.workplane(offset=-63/2).moveTo(57.5,94.5).box(79,11,63).union(w0.workplane(offset=-46/2).moveTo(-52,-87).box(90,26,46)).union(w0.sketch().segment((-22,72),(27,72)).arc((2,86),(-22,72)).assemble().finalize().extrude(6)).union(w1.workplane(offset=-111/2).moveTo(-6,-58).cylinder(111,7))