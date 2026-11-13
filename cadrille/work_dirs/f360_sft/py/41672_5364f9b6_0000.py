import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().arc((-99,-26),(-85,-52),(-58,-60)).segment((64,-60)).arc((85,-49),(100,-29)).segment((100,29)).arc((85,49),(64,60)).segment((-70,60)).arc((-93,41),(-99,13)).close().assemble().finalize().extrude(24).union(w0.workplane(offset=33/2).moveTo(-10.5,0).box(141,74,33))