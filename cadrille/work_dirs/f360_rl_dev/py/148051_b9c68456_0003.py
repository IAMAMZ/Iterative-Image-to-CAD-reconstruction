import cadquery as cq
w0=cq.Workplane('YZ',origin=(5,0,0))
r=w0.sketch().segment((-100,-35),(100,-35)).segment((-41,36)).close().assemble().finalize().extrude(-9)