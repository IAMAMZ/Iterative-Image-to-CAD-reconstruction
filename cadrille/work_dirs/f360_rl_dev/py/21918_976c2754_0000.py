import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-19))
r=w0.sketch().segment((-100,7),(-86,-22)).segment((93,-23)).segment((100,-7)).segment((96,7)).segment((69,11.5)).segment((49,-1)).segment((-69,-1)).segment((-76,23)).segment((-80,22)).close().assemble().finalize().extrude(2).union(w0.workplane(offset=38/2).moveTo(0,-22).box(164,1.5,38))