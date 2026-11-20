import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,35,0))
w1=cq.Workplane('YZ',origin=(-6,0,0))
r=w0.sketch().segment((-36,-6),(36,-6.5)).segment((36,67)).arc((0,100),(-36,67)).close().assemble().push([(0,65)]).circle(16.5,mode='s').finalize().extrude(-70).union(w1.sketch().circle(23).circle(16.5,mode='s').finalize().extrude(-94)).union(w1.workplane(offset=2/2).moveTo(0,29.5).box(1.5,6.5,1))