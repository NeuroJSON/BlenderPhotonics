function blender2mesh(filename)
%
% nodedata=surf2jmesh(filename)
%
% loading a trangular surface mesh from a file
%
% author: Qianqian Fang (q.fang at neu.edu)
%         Yuxuan Zhang (zhang.yuxuan1 at northeastern.edu)
%
% input:
%	 filename: path to the surface mesh file exported from Blender, data in JMesh format
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

blender=loadjson(filename, 'FastArrayParser',0);

if(blender.param.mergetol>0)
    [blender.MeshVertex3, blender.MeshPoly]=removedupnodes(blender.MeshVertex3, blender.MeshPoly, blender.param.mergetol);
end

if(blender.param.dorepair)
    [blender.MeshVertex3, blender.MeshPoly]=meshcheckrepair(blender.MeshVertex3, blender.MeshPoly, 'meshfix');
end

%% perform mesh generation
[node,elem]=s2m(blender.MeshVertex3,blender.MeshPoly,blender.param.keepratio,blender.param.maxvol,'tetgen1.5',[],[],blender.param.tetgenopt);
save('-v7',bpmwpath('meshdata.mat'),'node','elem');
disp(['begin to save region mesh'])

blendersavemesh(node,elem);