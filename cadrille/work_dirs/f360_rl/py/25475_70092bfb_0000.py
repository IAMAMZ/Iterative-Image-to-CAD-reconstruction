import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,13))
r=w0.sketch().push([(-95.5,0)]).rect(9,8.5).push([(0,0)]).rect(168,9.5).push([(95,0)]).rect(10,8.5).push([(95,0)]).rect(2.5,1.5).finalize().extrude(-26)