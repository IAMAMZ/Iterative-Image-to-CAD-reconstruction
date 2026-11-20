import cadquery as cq
w0=cq.Workplane('YZ',origin=(-49,0,0))
w1=cq.Workplane('ZX',origin=(0,-100,0))
r=w0.sketch().segment((-100,27),(0,-31)).segment((2,-29)).segment((-94,37.5)).segment((-95,57)).segment((-100,57)).close().assemble().finalize().extrude(-25).union(w0.sketch().segment((53,-57),(100,-56)).segment((100,-51)).segment((53,-51)).close().assemble().finalize().extrude(97)).union(w1.sketch().segment((24,33),(57,39)).segment((57,71)).segment((24,71)).close().assemble().finalize().extrude(6.5)).union(w1.workplane(offset=2/2).moveTo(49.5,66.5).box(13.5,1.5,1))