function blendersavemesh(node, elem, image)
%
% blendersavemesh(node,elem, image)
%
% Saving a tetrahedral mesh to JMesh file in BP's temporary folder
%
% author: Qianqian Fang (q.fang at neu.edu)
%
% input:
%	 node: the node coordinate list of a tetrahedral mesh (nn x 3)
%	 elem: the tetrahedral element list of the mesh (ne x 4)
%    image: the 3D voxel array of the mesh (labels)
%
% output:
%	 two JMesh files are saved under the temporary folder bpmwpath('')
%          volumemesh.jmsh: contains the tetrahedral mesh
%          regionmesh.jmsh: contains the surface of each individual regions/labels
%          imagemesh.jmsh: contains the voxel mesh
%
% license: GPLv3 or later, see LICENSE.txt for details
%
% reference:
%
% @article{BlenderPhotonics2022,
%   author = {Yuxuan Zhang and Qianqian Fang},
%   title = {{BlenderPhotonics: an integrated open-source software environment for three-dimensional meshing and photon simulations in complex tissues}},
%   volume = {27},
%   journal = {Journal of Biomedical Optics},
%   number = {8},
%   publisher = {SPIE},
%   pages = {1 -- 23},
%   year = {2022},
%   doi = {10.1117/1.JBO.27.8.083014},
%   URL = {https://doi.org/10.1117/1.JBO.27.8.083014}
% }
%
% -- this function is part of BlenderPhotonics (http://mcx.space/bp)
%

if(size(elem,2)<5)
    elem(:,5)=1;
end

meshdata=struct;
if(size(node,2)==3)
    meshdata.MeshVertex3=node;
else
    meshdata.MeshNode=node;
end

outputmesh=meshdata;

maxtag=max(elem(:,5))
for n = 1:maxtag
    fc1=volface(elem(elem(:,5)==n,1:4));
    outputmesh.(encodevarname(sprintf('MeshTri3(%d)',n)))=fc1;
end

if(maxtag==1)
    outputmesh.('MeshTri3')=outputmesh.(encodevarname('MeshTri3(1)'));
    outputmesh=rmfield(outputmesh,encodevarname('MeshTri3(1)'));
end

disp(['begin to save whole volumic mesh.'])
savejson('',outputmesh,'FileName',bpmwpath('regionmesh.jmsh'),'ArrayIndent',0);
faces = meshface(elem(:,1:4));

meshdata.MeshTri3=faces;
savejson('',meshdata,'FileName',bpmwpath('volumemesh.jmsh'),'ArrayIndent',0);

disp(['saving complete.'])
