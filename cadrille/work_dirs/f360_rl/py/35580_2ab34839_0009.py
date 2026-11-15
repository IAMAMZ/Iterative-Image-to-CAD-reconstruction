import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,54,0))
r=w0.sketch().push([(-62,-74)]).circle(10).push([(-62,75)]).circle(10).push([(62,75)]).circle(10).push([(62,-74)]).circle(10).finalize().extrude(-125).union(w0.sketch().push([(0,0)]).rect(175.5,200).finalize().extrude(18))