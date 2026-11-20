import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-25))
r=w0.sketch().circle(100).circle(57,mode='s').push([(-86,0)]).circle(6.5,mode='s').push([(-44,-76)]).circle(6).push([(-44,76)]).rect(8.5,6).push([(44,-76)]).circle(6.5).push([(44,76)]).circle(6).push([(86,0)]).circle(7.5).finalize().extrude(-14).union(w0.workplane(offset=65/2).cylinder(65,76))