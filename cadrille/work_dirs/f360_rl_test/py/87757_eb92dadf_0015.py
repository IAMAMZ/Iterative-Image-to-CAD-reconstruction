import cadquery as cq
w0=cq.Workplane('YZ',origin=(2,0,0))
r=w0.sketch().segment((-100,76),(-61,-57)).segment((84.5,-76)).segment((100,28.5)).close().assemble().finalize().extrude(-3.5)