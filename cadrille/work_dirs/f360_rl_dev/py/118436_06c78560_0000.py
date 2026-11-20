import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-50,-50),(7,-50)).segment((7,-21)).segment((50,-21)).segment((50,50)).segment((-5,50)).segment((-50,50)).close().assemble().finalize().extrude(-200)