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
%              MeshVertex3: an Nnx3 array for vertex coordinates
%              MeshTri3: an Nex3 integer array for triangular surface elements
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

if(regexp(filename,'\.[Oo][Ff][Ff]$'))
    [nodedata.MeshVertex3, nodedata.MeshTri3]=readoff(filename);
elseif(regexp(filename,'\.[Mm][Ee][Dd][Ii][Tt]$'))
    [nodedata.MeshVertex3, elem]=readmedit(filename);
    nodedata.MeshTri3=volface(elem(:,1:4));
elseif(regexp(filename,'\.[Ee][Ll][Ee]$'))
    [pathstr,name,ext] = fileparts(filename);
    [nodedata.node, elem]=readtetgen(fullfile(pathstr,name));
    nodedata.MeshTri3=volface(elem(:,1:4));
elseif(regexp(filename,'\.[Jj][Mm][Ee]*[Ss][Hh]$'))
    nodedata=loadjson(filename);
elseif(regexp(filename,'\.[Bb][Mm][Ee]*[Ss][Hh]$'))
    nodedata=loadbj(filename);
elseif(regexp(filename,'\.[Jj][Ss][Oo][Nn]$'))
    nodedata=loadjson(filename);
end
