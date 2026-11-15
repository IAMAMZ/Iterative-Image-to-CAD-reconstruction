import cadquery as cq
w0=cq.Workplane('XY',origin=(0,0,-0))
r=w0.sketch().circle(100).push([(-80,26)]).circle(7.5,mode='s').push([(0,0)]).circle(62,mode='s').push([(-50,-70)]).circle(8,mode='s').push([(0,86)]).circle(7.5,mode='s').push([(50,-70)]).circle(8.5,mode='s').push([(80,26)]).circle(7.5,mode='s').finalize().extrude(1.5)