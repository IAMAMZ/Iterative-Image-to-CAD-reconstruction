import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,54,0))
w1=cq.Workplane('XY',origin=(0,0,-88))
r=w0.sketch().segment((-87,-47),(-42,-47)).segment((-11,-100)).segment((89,-42)).segment((74,-19)).segment((60,-33)).segment((-11,-85)).segment((-79,27)).segment((-12,77)).segment((37,31)).segment((46,32)).segment((12,92)).segment((-12,80)).segment((-89,100)).close().assemble().push([(-57,67)]).rect(50.5,37.5,mode='s').finalize().extrude(-107).union(w0.workplane(offset=-17/2).moveTo(82,-36.5).box(8,1.5,6.5)).union(w1.workplane(offset=2/2).moveTo(92.5,4.5).box(7.5,1.5,1))