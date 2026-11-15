import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,10,0))
w1=cq.Workplane('YZ',origin=(-31,0,0))
r=w0.sketch().circle(30).circle(24,mode='s').finalize().extrude(-102).union(w1.sketch().segment((4,-100),(77,-100)).arc((86,-92),(92,-82)).segment((92,86)).arc((86,95),(77,100)).segment((4,100)).close().assemble().finalize().extrude(62))