import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
r=w0.sketch().push([(0,-47)]).rect(200,27).push([(0,40)]).rect(200,40).finalize().extrude(-200)