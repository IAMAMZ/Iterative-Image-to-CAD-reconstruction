import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-7,0))
r=w0.sketch().segment((-100,-2),(-70,-2)).segment((-73,-16)).segment((-56,-16)).arc((-61,0),(-56,16)).segment((-100,16)).close().assemble().reset().face(w0.sketch().segment((-48,-2),(100,-2)).segment((100,16)).segment((-48,16)).arc((-43,0),(-48,-2)).assemble()).finalize().extrude(14)