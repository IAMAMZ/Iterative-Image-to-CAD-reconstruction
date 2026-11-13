import cadquery as cq
w0=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().segment((-100,-73),(100,-73)).segment((67,72.5)).segment((-86.5,73)).segment((-87,41)).segment((-92,11)).close().assemble().finalize().extrude(-12.5)