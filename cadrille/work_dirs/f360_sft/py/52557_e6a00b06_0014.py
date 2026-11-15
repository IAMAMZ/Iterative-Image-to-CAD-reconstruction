import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().circle(60).reset().face(w0.sketch().arc((-28,11),(2,-29),(24,16)).segment((24,18)).segment((21,18)).arc((0,26),(-21,18)).segment((-28,18)).close().assemble(),mode='s').finalize().extrude(200)