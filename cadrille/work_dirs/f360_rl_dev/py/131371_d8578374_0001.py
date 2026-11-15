import cadquery as cq
w0=cq.Workplane('YZ',origin=(67,0,0))
r=w0.sketch().rect(200,200).circle(14.5,mode='s').finalize().extrude(-146.5).union(w0.sketch().rect(186.5,18.5).finalize().extrude(-11)).union(w0.sketch().rect(190.5,180.5).push([(-72,71)]).circle(8.5,mode='s').finalize().extrude(-11.5)).union(w0.sketch().circle(62).circle(14.5,mode='s').finalize().extrude(11.5))