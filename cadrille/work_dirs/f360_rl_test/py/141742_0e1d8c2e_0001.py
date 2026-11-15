import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,2))
w1=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().push([(0,-0)]).rect(115,200).finalize().extrude(-13).union(w0.workplane(offset=8/2).moveTo(-50.5,92.5).box(11.5,5.5,8)).union(w1.sketch().segment((-11,-57),(4,-57)).segment((4,-6)).segment((-2,0)).segment((4,11.5)).segment((4,57)).segment((-11,57)).close().assemble().finalize().extrude(200)).union(w1.workplane(offset=2/2).moveTo(8,0.5).box(1.5,1.5,1))