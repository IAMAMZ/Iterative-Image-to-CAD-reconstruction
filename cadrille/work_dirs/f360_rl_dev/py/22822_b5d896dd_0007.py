import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().arc((-17.5,-83),(0,-100),(17.5,-83)).segment((17.5,83)).arc((0,100),(-17,83)).close().assemble().finalize().extrude(6).union(w0.sketch().push([(0,-83)]).circle(7).circle(3.5).push([(0,83)]).circle(7.5).finalize().extrude(15.5))