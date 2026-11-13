import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,42))
r=w0.sketch().push([(-29,0)]).circle(70).circle(50,mode='s').reset().face(w0.sketch().segment((33,-16),(59,-19)).segment((69,-20)).arc((87,-15),(100,-6.5)).segment((100,8.5)).segment((84,15)).segment((69,20)).segment((40,16)).close().assemble()).finalize().extrude(-84)