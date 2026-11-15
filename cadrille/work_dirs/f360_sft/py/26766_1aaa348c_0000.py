import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-100))
r=w0.sketch().segment((-27,-2),(-14,-25)).segment((14,-25)).segment((27,-3)).segment((14,25)).segment((-14,25)).arc((-19,11),(-27,-2)).assemble().finalize().extrude(31).union(w0.workplane(offset=200/2).cylinder(200,15))