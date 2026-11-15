import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,47))
r=w0.sketch().segment((-100,0),(-50,-87)).segment((50,-86.5)).segment((100,0)).segment((50,86.5)).segment((-50,86.5)).close().assemble().finalize().extrude(-94)