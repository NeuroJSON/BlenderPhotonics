function blendersavemesh(node,elem)

if(size(elem,2)<5)
    elem(:,5)=1;
end

outputmesh=containers.Map();
outputmesh('MeshNode')=node;
maxtag=max(elem(:,5))
for n = 1:maxtag
    fc1=volface(elem(elem(:,5)==n,1:4));
    outputmesh(sprintf('MeshSurf(%d)',n))=fc1;
end
if(maxtag==1)
    outputmesh('MeshSurf')=outputmesh('MeshSurf(1)');
    remove(outputmesh,'MeshSurf(1)');
end
disp(['begin to save whole volumic mesh.'])
savejson('',outputmesh,'FileName',bpmwpath('regionmesh.jmsh'),'ArrayIndent',0);
faces = meshface(elem(:,1:4));
savejmesh(node,faces,[],bpmwpath('volumemesh.jmsh'),'ArrayIndent',0);
disp(['saving complete.'])