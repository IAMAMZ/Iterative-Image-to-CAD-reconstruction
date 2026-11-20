import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,37))
r=w0.sketch().push([(-50.5,0)]).rect(5,200).push([(50,-0)]).rect(4.5,200).finalize().extrude(-74)