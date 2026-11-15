import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,16,0))
r=w0.sketch().segment((-59,-100),(59,-100)).segment((59,10)).segment((59,100)).segment((-59,100)).close().assemble().finalize().extrude(-32).union(w0.sketch().push([(0,-67)]).rect(8.5,6.5).push([(42,64.5)]).rect(32.5,4.5).finalize().extrude(-4))