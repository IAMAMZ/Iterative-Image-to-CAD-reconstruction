import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-39))
w1=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-100,18),(-94,10)).arc((-87,8),(-87,1)).segment((-83,-4)).arc((-79,1),(-79,8)).segment((-74,8)).segment((-74,10)).segment((-79,10)).arc((-83,20),(-94,23)).close().assemble().finalize().extrude(79).union(w0.sketch().arc((-77,10),(-66,-20),(-40,-38)).segment((100,-38)).segment((100,-14)).segment((-16,-14)).close().assemble().finalize().extrude(79)).union(w1.sketch().arc((-21,-34),(6,0),(-21,34)).close().assemble().finalize().extrude(-11))