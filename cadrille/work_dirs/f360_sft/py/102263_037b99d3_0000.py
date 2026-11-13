import cadquery as cq
w0=cq.Workplane('ZX',origin=(0,-55,0))
w1=cq.Workplane('YZ',origin=(11,0,0))
r=w0.sketch().push([(0,-42.5)]).rect(72,115).push([(0,-66)]).circle(10,mode='s').finalize().extrude(28).union(w0.sketch().push([(0,55)]).rect(70,90).circle(10,mode='s').finalize().extrude(117)).union(w1.sketch().segment((-63,-35),(-26,-35)).segment((-26,35)).segment((-55,35)).segment((-55,16)).segment((-63,16)).close().assemble().finalize().extrude(-40))