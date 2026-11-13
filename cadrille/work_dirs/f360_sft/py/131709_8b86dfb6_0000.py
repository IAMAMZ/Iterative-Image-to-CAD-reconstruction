import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
r=w0.sketch().arc((-100,-37),(-91,-47),(-77,-46)).arc((-18,-64),(33,-26)).segment((33,-41)).segment((100,-41)).segment((100,41)).segment((33,41)).segment((33,37)).arc((-18,64),(-70,44)).arc((-85,47),(-100,43)).segment((-100,33)).arc((-90,35),(-81,33)).arc((-79,34),(-77,34)).arc((29,-5),(-78,-37)).close().assemble().finalize().extrude(-40)