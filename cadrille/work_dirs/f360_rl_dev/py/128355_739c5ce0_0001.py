import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-71.5,-37),(71.5,-37)).segment((71.5,37)).segment((67,37)).segment((66,-32.5)).segment((-71,-32)).close().assemble().finalize().extrude(-200)