import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,4,0))
w1=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().push([(0,-87)]).rect(15,26).finalize().extrude(-7.5).union(w1.workplane(offset=-174/2).moveTo(0,0).cylinder(174,4)).union(w1.workplane(offset=-20/2).moveTo(0,-0.5).box(3,7.5,20)).union(w1.workplane(offset=-2/2).moveTo(0,0.5).box(1.5,1.5,1))