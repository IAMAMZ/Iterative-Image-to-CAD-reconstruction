import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-67))
r=w0.sketch().segment((-27,-1),(-13,-24)).segment((13,-24)).segment((27,0)).segment((13,24)).segment((-13,24)).close().assemble().finalize().extrude(-33).union(w0.workplane(offset=167/2).moveTo(0,0).cylinder(167,15.5)).union(w0.workplane(offset=2/2).moveTo(0,18.5).box(1.5,1.5,1))