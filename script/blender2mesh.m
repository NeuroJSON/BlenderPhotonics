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

blendersavemesh(node,elem,regionmesh_fname, volumemesh_fname);