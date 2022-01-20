function blendersavemesh(node,elem)
%
% blendersavemesh(node,elem)
%
% Saving a tetrahedral mesh to JMesh file in BP's temporary folder
%
% author: Qianqian Fang (q.fang at neu.edu)
%
% input:
%	 node: the node coordinate list of a tetrahedral mesh (nn x 3)
%	 elem: the tetrahedral element list of the mesh (ne x 4)
%
% output:
%	 two JMesh files are saved under the temporary folder bpmwpath('')
%          volumemesh.jmsh: contains the tetrahedral mesh
%          regionmesh.jmsh: contains the surface of each individual regions/labels
%
% license: GPLv3 or later, see LICENSE.txt for details
%
% reference: 
% @article {BlenderPhotonics2022,
%  author = {Zhang, Yuxuang and Fang, Qianqian},
%  title = {{BlenderPhotonics -- a versatile environment for 3-D complex bio-tissue modeling and light transport simulations based on Blender}},
%  elocation-id = {2022.01.12.476124},
%  year = {2022},
%  doi = {10.1101/2022.01.12.476124},
%  publisher = {Cold Spring Harbor Laboratory},
%  URL = {https://www.biorxiv.org/content/early/2022/01/14/2022.01.12.476124},
%  eprint = {https://www.biorxiv.org/content/early/2022/01/14/2022.01.12.476124.full.pdf},
%  journal = {bioRxiv}
% }
%
% -- this function is part of BlenderPhotonics (http://mcx.space/bp)
%

if(size(elem,2)<5)
    elem(:,5)=1;
end

outputmesh=struct;
outputmesh.MeshNode=node;
maxtag=max(elem(:,5))
for n = 1:maxtag
    fc1=volface(elem(elem(:,5)==n,1:4));
    outputmesh.(encodevarname(sprintf('MeshSurf(%d)',n)))=fc1;
end

if(maxtag==1)
    outputmesh.('MeshSurf')=outputmesh.(encodevarname('MeshSurf(1)'));
    outputmesh=rmfield(outputmesh,encodevarname('MeshSurf(1)'));
end
disp(['begin to save whole volumic mesh.'])
savejson('',outputmesh,'FileName',bpmwpath('regionmesh.jmsh'),'ArrayIndent',0);
faces = meshface(elem(:,1:4));
savejmesh(node,faces,[],bpmwpath('volumemesh.jmsh'),'ArrayIndent',0);
disp(['saving complete.'])
