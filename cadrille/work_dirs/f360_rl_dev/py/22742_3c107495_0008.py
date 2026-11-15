import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-69,0))
r=w0.sketch().circle(100).finalize().extrude(13).union(w0.sketch().push([(74,0)]).circle(25).finalize().extrude(113)).union(w0.sketch().push([(74,0)]).rect(36.5,36.5).circle(12.5,mode='s').finalize().extrude(137))