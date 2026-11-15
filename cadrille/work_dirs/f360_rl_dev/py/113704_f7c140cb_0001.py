import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-66.5,-66.5),(66.5,-66.5)).segment((66.5,67)).segment((33,66)).segment((33,-34)).segment((-33,-34)).segment((-33,66.5)).segment((-66.5,66.5)).close().assemble().finalize().extrude(-200)