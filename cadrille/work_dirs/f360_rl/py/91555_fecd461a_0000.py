import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-35))
w1=cq.Workplane('YZ',origin=(-70,0,0))
r=w0.sketch().segment((-53,-25),(7,-25)).segment((10,-4)).segment((29,0)).segment((33,-25)).segment((92,-25)).arc((100,-6),(92,3)).segment((60,6)).segment((60,25)).segment((0,25)).segment((-8,7)).segment((-50,2)).segment((-59,-10)).close().assemble().finalize().extrude(-22).union(w1.sketch().segment((-25,-19),(3,-19)).segment((3,50)).segment((-1,56)).segment((-10,56)).segment((-25,51)).close().assemble().finalize().extrude(-30)).union(w1.workplane(offset=-30/2).moveTo(-9.5,0.5).box(27.5,1,1))