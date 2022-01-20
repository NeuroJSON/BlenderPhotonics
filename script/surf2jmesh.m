function nodedata=surf2jmesh(filename)
%
% nodedata=surf2jmesh(filename)
%
% loading a trangular surface mesh from a file
%
% author: Qianqian Fang (q.fang at neu.edu)
%
% input:
%	 filename: path to the surface mesh file, accept OFF (.off), Tetgen (.ele),
%                  JMesh (.jmsh/.json), binary JMesh (.bmsh) and INRIA Medit (.medit) files
%
% output:
%	 nodedata: a struct containing 
%              MeshNode: an Nnx3 array for vertex coordinates
%              MeshSurf: an Nex3 integer array for triangular surface elements
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

if(regexp(filename,'\.[Oo][Ff][Ff]$'))
    [nodedata.MeshNode, nodedata.MeshSurf]=readoff(filename);
elseif(regexp(filename,'\.[Mm][Ee][Dd][Ii][Tt]$'))
    [nodedata.MeshNode, elem]=readmedit(filename);
    nodedata.MeshSurf=volface(elem(:,1:4));
elseif(regexp(filename,'\.[Ee][Ll][Ee]$'))
    [pathstr,name,ext] = fileparts(filename);
    [nodedata.node, elem]=readtetgen(fullfile(pathstr,name));
    nodedata.MeshSurf=volface(elem(:,1:4));
elseif(regexp(filename,'\.[Jj][Mm][Ee]*[Ss][Hh]$'))
    nodedata=loadjson(filename);
elseif(regexp(filename,'\.[Bb][Mm][Ee]*[Ss][Hh]$'))
    nodedata=loadbj(filename);
elseif(regexp(filename,'\.[Jj][Ss][Oo][Nn]$'))
    nodedata=loadjson(filename);
end
