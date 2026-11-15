import cadquery as cq
w0=cq.Workplane('YZ',origin=(40,0,0))
r=w0.sketch().circle(100).circle(30,mode='s').finalize().extrude(-100).union(w0.sketch().circle(58).circle(29.5,mode='s').finalize().extrude(20)).union(w0.sketch().circle(58).circle(29.5,mode='s').finalize().extrude(20)).union(w0.workplane(offset=20/2).box(1.5,1.5,16.5))