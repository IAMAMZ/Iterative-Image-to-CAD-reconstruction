import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,44,0))
r=w0.sketch().segment((-100,-6),(-44,-90)).segment((56,-83)).segment((100,6.5)).segment((44,90)).segment((-56,83.5)).close().assemble().circle(65.5,mode='s').finalize().extrude(-87)