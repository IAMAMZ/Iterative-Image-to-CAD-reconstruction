import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,20,0))
r=w0.sketch().segment((-100,-58),(100,-58)).segment((100,30)).segment((47,31)).arc((0,58),(-48,30)).segment((-100,30)).close().assemble().circle(43,mode='s').finalize().extrude(-40)