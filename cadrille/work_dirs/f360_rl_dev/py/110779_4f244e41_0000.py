import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.sketch().segment((-79,-65),(0,-65)).segment((80,0)).segment((2,65.5)).segment((-79,65.5)).close().assemble().finalize().extrude(-200).union(w0.sketch().push([(-39,-44)]).rect(80.5,3.5).finalize().extrude(-29)).union(w0.workplane(offset=-10/2).moveTo(-40,44.5).box(1.5,3.5,9))