function nii2mesh(filename)

input=loadjson(filename);
niipath=input.niipath;

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

if(~isempty(regexp(niipath,'\.[jb]*nii(\.gz)*$|\.json$','match','ignorecase')))
    vol = loadjnifti(niipath);
elseif(~isempty(regexp(niipath,'\.hdr$|\.img$','match','ignorecase')))
    vol = loadnifti(niipath);
elseif(~isempty(regexp(niipath,'\.mat$','match','ignorecase')))
    tmp=load(niipath);
    vars=fieldnames(tmp);
    for i=1:length(vars)
        if(ndims(tmp.(vars{i}))==3)
            vol.NIFTIData=tmp.tmp.(vars{i});
            break;
        end
    end
end

opt=struct('radbound',jsonopt('radbound',10,input), 'distbound',jsonopt('distbound',1,input));
maxvol=jsonopt('maxvol',100,input);
method=jsonopt('method','cgalmesh',input);
isovalue=jsonopt('isovalue',0.5,input);

if(strcmp(method,'auto'))
    labelnum=length(unique(vol.NIFTIData));
    if(labelnum==2 || labelnum> 64)
        method='cgalsurf';
    else
        method='cgalmesh';
    end
    if(strcmp(method,'cgalmesh') && labelnum>64)
        vol.NIFTIData=uint8(vol.NIFTIData>isovalue);
    end
end

if(strcmp(method,'cgalmesh'))
    vol.NIFTIData=uint8(vol.NIFTIData);
    isovalue=[];
end

[node,elem,face]=v2m(vol.NIFTIData,isovalue,opt,maxvol,method);

%% post processing, scale mesh with the voxel size 0.1 mm
node=node(:,1:3);
elem(:,1:4)=meshreorient(node(:,1:3),elem(:,1:4));
save('-mat7-binary',bpmwpath('niimesh.mat'),'node','elem','face');

blendersavemesh(node,elem);