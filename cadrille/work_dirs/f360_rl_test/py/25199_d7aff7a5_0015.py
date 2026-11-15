import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-3))
r=w0.sketch().segment((0,49),(59,54)).segment((10,86)).segment((0,80)).close().assemble().finalize().extrude(-44).union(w0.sketch().circle(100).circle(33.5,mode='s').finalize().extrude(14.5)).union(w0.sketch().circle(100).circle(47,mode='s').finalize().extrude(51)).union(w0.workplane(offset=50/2).box(1.5,1.5,50))