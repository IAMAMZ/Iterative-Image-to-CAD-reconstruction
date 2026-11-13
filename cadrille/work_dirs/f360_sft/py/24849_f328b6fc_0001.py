import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-13,6),(4,6)).segment((4,-10)).segment((13,-10)).segment((13,10)).segment((-13,10)).close().assemble().finalize().extrude(200)