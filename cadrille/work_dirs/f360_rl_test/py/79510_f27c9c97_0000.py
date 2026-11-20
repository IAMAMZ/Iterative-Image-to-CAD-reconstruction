import cadquery as cq
w0=cq.Workplane('YZ',origin=(3,0,0))
r=w0.sketch().segment((-55.5,-100),(56,-100)).segment((-18,84)).segment((-6,87)).segment((-6.5,100)).segment((-55.5,100)).close().assemble().finalize().extrude(-5.5)