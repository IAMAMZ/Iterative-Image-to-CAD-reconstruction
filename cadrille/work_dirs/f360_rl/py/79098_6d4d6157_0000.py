import cadquery as cq
w0=cq.Workplane('YZ',origin=(12,0,0))
w1=cq.Workplane('YZ',origin=(7,0,0))
r=w0.sketch().push([(0,-82)]).circle(18.5).circle(15.5,mode='s').finalize().extrude(-28).union(w1.sketch().push([(0,87)]).circle(13).circle(8.5,mode='s').finalize().extrude(-14)).union(w1.workplane(offset=-14/2).moveTo(0,8.5).box(14,149.5,14)).union(w1.workplane(offset=-1/2).moveTo(15,97.5).box(1.5,1,1))