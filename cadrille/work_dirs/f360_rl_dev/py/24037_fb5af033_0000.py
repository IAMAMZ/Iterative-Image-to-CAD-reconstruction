import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-54.5,0))
w1=cq.Workplane('YZ',origin=(9,0,0))
r=w0.sketch().arc((-36.5,-69),(6,-100),(36.5,-64.5)).segment((36.5,69)).arc((-4,100),(-36,69)).close().assemble().push([(0,-63)]).circle(18,mode='s').push([(0,64)]).circle(18,mode='s').finalize().extrude(18).union(w1.sketch().segment((-39,-35),(29,-35)).arc((54,0),(29,35)).segment((-39,35)).close().assemble().push([(19,0)]).circle(18.5,mode='s').finalize().extrude(-18)).union(w1.workplane(offset=-2/2).moveTo(-47,0.5).box(13.5,1.5,1.5))