function blender2mesh

blender=loadjson(bpmwpath('blendermesh.json'));
blender

if(blender.mergetol>0)
    [blender.v, blender.f]=removedupnodes(blender.v, blender.f, blender.mergetol);
end

if(blender.dorepair)
    [blender.v, blender.f]=meshcheckrepair(blender.v, blender.f, 'meshfix');
end

%% perform mesh generation
[node,elem,face]=s2m(blender.v,blender.f,blender.keepratio,blender.maxvol,'tetgen1.5',[],[],blender.tetgenopt);
save('-mat7-binary',bpmwpath('meshdata.mat'),'node','elem','face');
disp(['begin to save region mesh'])

blendersavemesh(node,elem);