import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,80))
r=w0.sketch().circle(85).circle(40,mode='s').finalize().extrude(-160).union(w0.sketch().circle(100).circle(40,mode='s').finalize().extrude(-30)).union(w0.sketch().circle(100).circle(40,mode='s').finalize().extrude(-27))