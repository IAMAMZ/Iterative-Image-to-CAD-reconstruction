import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,8))
r=w0.sketch().segment((-100,-29),(-89,-29)).segment((51,4)).segment((74,5)).segment((100,29)).segment((97,29)).segment((69,14)).segment((50,14)).segment((-87,-23)).segment((-100,-25)).close().assemble().finalize().extrude(-16).union(w0.workplane(offset=-2/2).moveTo(-96.5,-26.5).box(5,3.5,2))