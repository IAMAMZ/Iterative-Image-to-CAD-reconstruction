import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,35.5,0))
r=w0.sketch().circle(37).circle(19,mode='s').finalize().extrude(-85).union(w0.sketch().rect(200,125).finalize().extrude(-70)).union(w0.workplane(offset=15/2).cylinder(15,23.5))