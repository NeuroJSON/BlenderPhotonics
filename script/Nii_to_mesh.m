load path.mat
test = loadnifti(path);

clear opt
for n = 1:max(test.NIFTIData(:))
    opt(n).keepratio=0.1;
    opt(n).radbound=5;
    opt(n).side='lower';
end

[node,elem,face]=vol2mesh(test.NIFTIData,1:size(test.NIFTIData,1),1:size(test.NIFTIData,2),1:size(test.NIFTIData,3),opt,100,1,'cgalmesh');
%% post processing, scale mesh with the voxel size 0.1 mm
node(:,4)=[];
elem(:,1:4)=meshreorient(node(:,1:3),elem(:,1:4));
save('-mat7-binary','meshdata.mat','node','elem','face');

for n = 1:max(elem(:,5))
    disp(["region ",num2str(n),' is saving...'])
    fc1=volface(elem(elem(:,5)==n,1:4));
    filename1 = ['./stlfile/',num2str(n), ".stl"];
    savestl(node,fc1,filename1)
    disp(['saving complete.'])
end

disp(['begin to save whole volumic mesh.'])
faces = meshface(elem(:,1:4));
savestl(node,faces,'volumic_mesh.stl');
disp(['saving complete.'])
