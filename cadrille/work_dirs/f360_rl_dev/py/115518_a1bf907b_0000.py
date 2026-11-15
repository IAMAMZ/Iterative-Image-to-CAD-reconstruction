import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-13,0))
r=w0.sketch().segment((-100,37),(-78,35)).segment((0,-37)).segment((59,-92)).segment((100,-98)).segment((100,95.5)).segment((55,98)).segment((-1,78)).segment((-70,61.5)).segment((-78,54)).segment((-97,54.5)).close().assemble().finalize().extrude(19).union(w0.workplane(offset=25/2).moveTo(-57,39.5).box(20.5,7.5,25))