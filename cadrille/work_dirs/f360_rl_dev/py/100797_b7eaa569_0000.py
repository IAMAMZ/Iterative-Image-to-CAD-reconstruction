import cadquery as cq
w0=cq.Workplane('YZ',origin=(19,0,0))
r=w0.sketch().segment((-54,-72),(-27,-100)).segment((27,-100)).segment((54,-72)).segment((54.5,-67)).segment((54.5,72.5)).segment((27,100)).segment((-54,100)).segment((-54,62)).segment((16,62)).segment((15,-62)).segment((-11,-62)).segment((-54,-52)).close().assemble().finalize().extrude(-37)