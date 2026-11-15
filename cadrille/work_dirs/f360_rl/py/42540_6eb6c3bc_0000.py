import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
w1=cq.Workplane('YZ',origin=(9,0,0))
r=w0.sketch().segment((-79,-87),(29,-87)).segment((29,10)).segment((-30,37)).segment((-30,87.5)).segment((-79,87.5)).close().assemble().finalize().extrude(-200).union(w1.workplane(offset=-19/2).moveTo(60,-37).box(38.5,15.5,19)).union(w1.workplane(offset=-8/2).moveTo(60,-37).box(19.5,10,1))