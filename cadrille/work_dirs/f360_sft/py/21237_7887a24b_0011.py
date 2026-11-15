import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-94))
w1=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().circle(21).circle(18,mode='s').finalize().extrude(194).union(w1.sketch().arc((13,-13),(21,0),(13,13)).segment((13,10)).arc((19,0),(13,-10)).close().assemble().finalize().extrude(19))