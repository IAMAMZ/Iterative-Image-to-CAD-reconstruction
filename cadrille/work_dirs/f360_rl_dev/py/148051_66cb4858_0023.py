import cadquery as cq
w0=cq.Workplane('YZ',origin=(6,0,0))
r=w0.sketch().segment((-5,-100),(5.5,-100)).segment((5.5,97)).segment((5,100)).segment((-5,100)).segment((-5,97)).segment((3.5,97)).segment((2.5,-97)).segment((-5,-97.5)).close().assemble().finalize().extrude(-13)