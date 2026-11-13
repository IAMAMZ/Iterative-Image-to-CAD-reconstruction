import cadquery as cq
w0=cq.Workplane('YZ',origin=(-100,0,0))
r=w0.sketch().segment((-100,-84),(100,-84)).segment((100,84)).segment((-67,84)).close().assemble().finalize().extrude(200)