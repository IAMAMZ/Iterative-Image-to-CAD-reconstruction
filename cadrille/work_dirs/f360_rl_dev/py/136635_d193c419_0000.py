import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,9))
r=w0.sketch().rect(83.5,200).push([(0,20)]).rect(13.5,17.5,mode='s').finalize().extrude(-17).union(w0.workplane(offset=-9/2).box(80.5,196.5,9)).union(w0.workplane(offset=-6/2).box(7.5,196.5,6))