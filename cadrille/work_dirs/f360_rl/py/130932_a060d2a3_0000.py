import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,80))
w1=cq.Workplane('ZX',origin=(0,-60,0))
r=w0.sketch().segment((-44,-100),(81.5,-100)).segment((81,-60)).segment((46,-60)).segment((46,-13)).segment((27,-13)).segment((27,-60)).segment((-26,-60)).segment((-26,-13)).segment((-44,-13)).close().assemble().finalize().extrude(-160).union(w0.workplane(offset=-4.5/2).moveTo(0,40).box(92,120,4.5)).union(w1.sketch().push([(0,0)]).rect(162,162).push([(-62,57.5)]).rect(7,7).finalize().extrude(-40))