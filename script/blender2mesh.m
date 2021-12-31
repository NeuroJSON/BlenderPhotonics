function blender2mesh(filename)

blender=loadjson(filename, 'FastArrayParser',0);

if(blender.param.mergetol>0)
    [blender.MeshNode, blender.MeshPoly]=removedupnodes(blender.MeshNode, blender.MeshPoly, blender.param.mergetol);
end

if(blender.param.dorepair)
    [blender.MeshNode, blender.MeshPoly]=meshcheckrepair(blender.MeshNode, blender.MeshPoly, 'meshfix');
end

%% perform mesh generation
[node,elem,face]=s2m(blender.MeshNode,blender.MeshPoly,blender.param.keepratio,blender.param.maxvol,'tetgen1.5',[],[],blender.param.tetgenopt);
save('-mat7-binary',bpmwpath('meshdata.mat'),'node','elem','face');
disp(['begin to save region mesh'])

blendersavemesh(node,elem);