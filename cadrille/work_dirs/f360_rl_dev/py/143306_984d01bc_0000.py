import cadquery as cq
w0=cq.Workplane('YZ',origin=(26,0,0))
w1=cq.Workplane('YZ',origin=(39,0,0))
r=w0.sketch().circle(100).circle(95,mode='s').finalize().extrude(-39.5).union(w1.sketch().arc((73,-66),(100,0),(73,66)).segment((73,59.5)).arc((95,-6),(73,-61.5)).close().assemble().finalize().extrude(-77.5)).union(w1.workplane(offset=-7/2).moveTo(97,0.5).box(2.5,1.5,7))