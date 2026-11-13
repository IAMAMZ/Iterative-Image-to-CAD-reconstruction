import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-59,0))
w1=cq.Workplane('XY',origin=(0,0,57))
r=w0.sketch().segment((-88,-35),(27,-35)).arc((55,-59),(88,-55)).segment((88,-23)).segment((88,55)).arc((55,51),(27,34)).segment((-88,34)).close().assemble().push([(-54,-13)]).circle(5,mode='s').finalize().extrude(9).union(w0.sketch().push([(69,-82)]).circle(18).push([(70,81)]).circle(19).finalize().extrude(118)).union(w1.workplane(offset=-87/2).moveTo(-83,40).cylinder(87,17))