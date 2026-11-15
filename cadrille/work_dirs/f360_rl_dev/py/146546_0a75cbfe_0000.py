import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,8,0))
r=w0.sketch().segment((-23,-7),(-10,-79)).segment((-10,-100)).segment((9,-86)).segment((14,-43)).segment((16,-23)).segment((16,0)).segment((23,77)).segment((23,100)).segment((8,100)).segment((-1,76)).segment((-16,31)).segment((-23,6)).close().assemble().push([(0,-67)]).circle(3,mode='s').finalize().extrude(-16)