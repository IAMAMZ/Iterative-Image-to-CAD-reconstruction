import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-8,0))
r=w0.sketch().push([(-89,-0)]).rect(8,200).push([(0,94.5)]).rect(183,11).push([(89,-0)]).rect(8.5,200).finalize().extrude(4.5).union(w0.sketch().push([(-38,-54)]).circle(31).push([(38,-54)]).circle(30).finalize().extrude(17))