function blender2mesh

load(bpmwpath('blendermesh.mat'));

f = f+1; % make index start from 1
% f and v stores the surface patch faces and nodes

if(mergetol>0)
    [v,f]=removedupnodes(v,f, mergetol);
end

if(dorepair)
    [v,f]=meshcheckrepair(v,f, 'meshfix');
end

%% perform mesh generation
[node,elem,face]=s2m(v,f,keepratio,maxvol,'tetgen1.5',[],[],tetgenopt);
save('-mat7-binary',bpmwpath('meshdata.mat'),'node','elem','face');
disp(['begin to save region mesh'])

if(size(elem,2)<5)
    elem(:,5)=1;
end

for n = 1:max(elem(:,5))
    disp(["region ",num2str(n),' is saving...'])
    fc1=volface(elem(elem(:,5)==n,1:4));
    filename = bpmwpath([num2str(n), ".stl"]);
    savestl(node,fc1,filename);
    disp(['saving complete.'])
end
disp(['begin to save whole volumic mesh.'])
faces = meshface(elem(:,1:4));
savestl(node,faces,bpmwpath('volumic_mesh.stl'));
disp(['saving complete.'])
