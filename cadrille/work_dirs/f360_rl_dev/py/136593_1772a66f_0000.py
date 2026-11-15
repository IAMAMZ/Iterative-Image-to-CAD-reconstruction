import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,100))
w1=cq.Workplane('ZX',origin=(0,-6.5,0))
r=w0.sketch().segment((-55,-7),(55,-7)).segment((55,7)).segment((47,7)).segment((42,-4)).segment((-46,-4)).segment((-48,7)).segment((-55,6.5)).close().assemble().finalize().extrude(-200).union(w1.sketch().push([(69.5,-0)]).rect(61,109).push([(65.5,0)]).rect(51.5,26.5,mode='s').finalize().extrude(4.5)).union(w1.workplane(offset=1/2).moveTo(96.5,0.5).box(1.5,1.5,1))