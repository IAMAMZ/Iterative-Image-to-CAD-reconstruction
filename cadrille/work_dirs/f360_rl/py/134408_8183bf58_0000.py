import cadquery as cq
w0=cq.Workplane('YZ',origin=(3,0,0))
r=w0.sketch().segment((-42,-100),(42,-100)).segment((42,-35)).segment((11,-34)).segment((11,78)).segment((28,78)).segment((28.5,100)).segment((-5,100)).segment((-19,89)).segment((-42,67.5)).segment((-42,62)).close().assemble().push([(-10,15)]).circle(11,mode='s').finalize().extrude(-6)