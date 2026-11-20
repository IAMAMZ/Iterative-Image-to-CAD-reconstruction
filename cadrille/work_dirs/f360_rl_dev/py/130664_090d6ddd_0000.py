import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,25,0))
r=w0.sketch().rect(200,178.5).push([(-78,-0)]).circle(6.5,mode='s').push([(-24.5,9.5)]).rect(23,50.5,mode='s').push([(0,-62)]).circle(7,mode='s').push([(2,62)]).circle(6.5,mode='s').push([(62,-31)]).rect(4.5,4).finalize().extrude(-48.5).union(w0.workplane(offset=-8/2).box(1.5,1,6))