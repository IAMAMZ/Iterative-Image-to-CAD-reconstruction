import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,46))
r=w0.sketch().rect(107,183).push([(0,-37)]).circle(16.5,mode='s').push([(0,50)]).circle(16.5,mode='s').finalize().extrude(-146).union(w0.sketch().rect(107,184).push([(25,0)]).rect(11.5,1).finalize().extrude(54)).union(w0.workplane(offset=54/2).box(1.5,1.5,54))