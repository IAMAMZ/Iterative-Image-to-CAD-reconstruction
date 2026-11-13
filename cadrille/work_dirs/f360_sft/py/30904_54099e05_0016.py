import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((-12,-9),(-5,-9)).arc((-4,-10),(-2,-10)).segment((-2,10)).arc((-4,10),(-5,9)).segment((-12,9)).close().assemble().reset().face(w0.sketch().arc((2,-10),(4,-10),(5,-9)).segment((12,-9)).segment((12,9)).segment((5,9)).arc((4,10),(2,10)).close().assemble()).finalize().extrude(200)