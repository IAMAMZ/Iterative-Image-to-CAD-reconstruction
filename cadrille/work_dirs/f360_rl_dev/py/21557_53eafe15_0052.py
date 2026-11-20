import cadquery as cq
w0=cq.Workplane('YZ',origin=(100,0,0))
r=w0.workplane(offset=-200/2).cylinder(200,16).union(w0.sketch().segment((-23,-1),(-13,-20)).segment((13,-20)).segment((23,0)).segment((13,20)).segment((-13.5,20)).close().assemble().finalize().extrude(-19)).union(w0.workplane(offset=-7/2).box(11.5,19.5,7))