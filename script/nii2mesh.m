function nii2mesh

load(bpmwpath('niipath.mat'));

if(~isempty(regexp(niipath,'^http','match','ignorecase')))
    suffix=regexp(niipath,'\.[jb]*nii(\.gz)*|\.mat|\.json','match','ignorecase');
    if(isempty(suffix))
        suffix='.json';
    else
        suffix=suffix{1};
    end
    urlwrite(niipath,bpmwpath(['volumedata',suffix]));
    niipath=bpmwpath(['volumedata',suffix]);
end

if(~isempty(regexp(niipath,'\.[jb]*nii(\.gz)*$|\.json','match','ignorecase')))
    test = loadjnifti(niipath);
elseif(~isempty(regexp(niipath,'\.mat$','match','ignorecase')))
    tmp=load(niipath);
    vars=fieldnames(tmp);
    for i=1:length(vars)
        if(ndims(tmp.(vars{i}))==3)
            test.NIFTIData=tmp.tmp.(vars{i});
            break;
        end
    end
end

if(exist('opt','var')==0)
    opt=struct('radbound',5, 'distbound',1);
end

[node,elem,face]=vol2mesh(test.NIFTIData,1:size(test.NIFTIData,1),1:size(test.NIFTIData,2),1:size(test.NIFTIData,3),opt,100,1,'cgalmesh');
%% post processing, scale mesh with the voxel size 0.1 mm
node(:,4)=[];
elem(:,1:4)=meshreorient(node(:,1:3),elem(:,1:4));
save('-mat7-binary',bpmwpath('niimesh.mat'),'node','elem','face');

for n = 1:max(elem(:,5))
    disp(["region ",num2str(n),' is saving...'])
    fc1=volface(elem(elem(:,5)==n,1:4));
    filename = bpmwpath([num2str(n), ".stl"]);
    savestl(node,fc1,filename)
    disp(['saving complete.'])
end

disp(['begin to save whole volumic mesh.'])
faces = meshface(elem(:,1:4));
savestl(node,faces,bpmwpath('volumic_mesh.stl'));
disp(['saving complete.'])
