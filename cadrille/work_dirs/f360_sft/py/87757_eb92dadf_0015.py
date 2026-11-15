import cadquery as cq
w0=cq.Workplane('YZ',origin=(2,0,0))
r=w0.sketch().segment((-100,76),(-62,-57)).segment((84,-76)).segment((100,29)).close().assemble().finalize().extrude(-4)