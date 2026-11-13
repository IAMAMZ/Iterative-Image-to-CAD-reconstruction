import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,90))
w1=cq.Workplane('YZ',origin=(-18,0,0))
r=w0.sketch().arc((-5,71),(27,28),(17,-26)).arc((85,45),(-5,71)).assemble().push([(35,-56)]).circle(30).finalize().extrude(4).union(w0.workplane(offset=10/2).moveTo(35,-56).cylinder(10,21)).union(w1.sketch().arc((-52,-94),(-41,-94),(-52,-92)).arc((-50,-93),(-52,-94)).assemble().finalize().extrude(-68))