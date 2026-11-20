import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-2.5,0))
r=w0.sketch().segment((-100,-93),(-89,-100)).segment((89,-100)).segment((100,-93)).segment((100,93)).segment((89,100)).segment((-89,100)).segment((-100,93)).close().assemble().finalize().extrude(3).union(w0.sketch().rect(146.5,139.5).finalize().extrude(4))