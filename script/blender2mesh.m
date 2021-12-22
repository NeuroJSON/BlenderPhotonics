%% load the sample data
load result.mat
f = f+1; % make index start from 1
% f and v stores the surface patch faces and nodes

%% perform mesh generation
[node,elem,face]=s2m(v,f,ratio,maxv,'tetgen1.5');
save('-mat7-binary','meshdata.mat','node','elem','face');
disp(['begin to save region mesh'])

for n = 1:max(elem(:,5))
    disp(["region ",num2str(n),' is saving...'])
    fc1=volface(elem(elem(:,5)==n,1:4));
    filename = ['./stlfile/', num2str(n), ".stl"];
    savestl(node,fc1,filename);
    disp(['saving complete.'])
end
disp(['begin to save whole volumic mesh.'])
faces = meshface(elem(:,1:4));
savestl(node,faces,'volumic_mesh.stl');
disp(['saving complete.'])
