import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-16))
r=w0.sketch().arc((-100,-31),(-91,-50),(-69,-60)).segment((69,-60)).arc((93,-46),(100,-23.5)).segment((100,31)).arc((91,50),(69,60)).segment((-69,60)).segment((-79,60)).arc((-95,45),(-100,31)).close().assemble().finalize().extrude(24).union(w0.workplane(offset=32/2).box(150.5,75,32))