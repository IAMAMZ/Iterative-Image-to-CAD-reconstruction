import cadquery as cq
w0=cq.Workplane('YZ',origin=(3,0,0))
r=w0.sketch().segment((-55,-100),(55,-100)).segment((-20,83)).segment((-7,87)).segment((-7,100)).segment((-55,100)).close().assemble().finalize().extrude(-6)