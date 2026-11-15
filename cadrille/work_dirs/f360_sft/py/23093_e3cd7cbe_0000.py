import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,5,0))
r=w0.sketch().segment((-100,-13),(85,-13)).segment((85,-10)).segment((83,-10)).segment((83,-2)).segment((-72,-2)).segment((-72,21)).segment((-86,21)).segment((-86,-2)).segment((-100,-2)).close().assemble().finalize().extrude(-10).union(w0.workplane(offset=-3/2).moveTo(10.5,-7).box(179,6,3))