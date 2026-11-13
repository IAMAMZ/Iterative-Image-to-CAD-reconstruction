import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-35))
w1=cq.Workplane('YZ',origin=(-71,0,0))
r=w0.sketch().segment((-48,-26),(4,-26)).arc((6,-16),(4,-6)).segment((34,-6)).arc((45,-24),(67,-22)).arc((99,-16),(78,6)).arc((68,10),(58,9)).arc((57,21),(47,27)).segment((-7,27)).segment((-7,26)).arc((-11,15),(-7,4)).segment((-7,3)).arc((-28,6),(-48,-3)).arc((-58,-15),(-48,-26)).assemble().finalize().extrude(-21).union(w1.sketch().arc((-25,-19),(-10,-31),(2,-16)).segment((2,45)).arc((-11,56),(-25,45)).close().assemble().finalize().extrude(-29))