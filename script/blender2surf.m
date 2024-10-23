function blender = blender2surf(filename)
%
% blender2surf(filename)
%
% Load a JMesh surface mesh file and perform a specified surface processing
%
% author: Qianqian Fang (q.fang at neu.edu)
%
% input:
%    filename: the path to a JMesh file containing a surface mesh, the JSON tree must contain
%           param.action: a string can be 'repair','smooth','reorient','simplify','remesh',
%                 'boolean-and','boolean-or','boolean-xor','boolean-diff','boolean-first',
%                 'boolean-second','boolean-decouple'
%           param.level: a single number to be used for the respective action;
%                 for 'smooth': this indicates number of iterations
%                 for 'simplify': this indicates percentage of edges to be kept
%                 for 'boolean-*': a negative value (-1) suggests flipping the two input surfaces
%           the structure should contain a single or multiple JMesh objects object(i), each should have
%           object(i).MeshVertex3: an Nnx3 array for vertex coordinates
%           object(i).MeshTri3: an Nex3 integer array for triangular surface elements
%
% output:
%    the processed surface mesh is saved as a JMesh file under the temporary folder bpmwpath('')
%          surfacemesh.jmsh: contains the processed surface mesh
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

blender = loadjson(filename, 'FastArrayParser', 0);

objs = blender.MeshGroup;
if (isstruct(objs) && length(objs) == 1)
    objs = {objs};
end

if (~isempty(regexp(blender.param.action, 'repair')))
    for i = 1:length(objs)
        if (~iscell(objs{i}.MeshTri3))
            [objs{i}.MeshVertex3, objs{i}.MeshTri3] = meshcheckrepair(objs{i}.MeshVertex3, objs{i}.MeshTri3, 'meshfix');
        end
    end
end

if (~isempty(regexp(blender.param.action, 'smooth')))
    for i = 1:length(objs)
        if (~iscell(objs{i}.MeshTri3))
            objs{i}.MeshVertex3 = sms(objs{i}.MeshVertex3, objs{i}.MeshTri3, blender.param.level);
        end
    end
end

if (~isempty(regexp(blender.param.action, 'reorient')))
    for i = 1:length(objs)
        if (~iscell(objs{i}.MeshTri3))
            [objs{i}.MeshVertex3, objs{i}.MeshTri3] = surfreorient(objs{i}.MeshVertex3, objs{i}.MeshTri3);
        end
    end
end

if (~isempty(regexp(blender.param.action, 'simplify')))
    for i = 1:length(objs)
        if (~iscell(objs{i}.MeshTri3))
            [objs{i}.MeshVertex3, objs{i}.MeshTri3] = meshresample(objs{i}.MeshVertex3, objs{i}.MeshTri3, blender.param.level);
        end
    end
end

if (~isempty(regexp(blender.param.action, 'remesh')))
    for i = 1:length(objs)
        if (~iscell(objs{i}.MeshTri3))
            [objs{i}.MeshVertex3, objs{i}.MeshTri3] = surfboolean(objs{i}.MeshVertex3, objs{i}.MeshTri3, 'remesh', objs{i}.MeshVertex3, objs{i}.MeshTri3);
        end
    end
end

op = regexp(blender.param.action, 'boolean-[a-zA-Z]+', 'match');

if (~isempty(op))
    if (length(objs) == 2)
        if (blender.param.level >= 0)
            [objs{1}.MeshVertex3, objs{1}.MeshTri3] = surfboolean(objs{1}.MeshVertex3, objs{1}.MeshTri3, regexprep(op{1}, 'boolean-', ''), objs{2}.MeshVertex3, objs{2}.MeshTri3);
        else
            [objs{1}.MeshVertex3, objs{1}.MeshTri3] = surfboolean(objs{2}.MeshVertex3, objs{2}.MeshTri3, regexprep(op{1}, 'boolean-', ''), objs{1}.MeshVertex3, objs{1}.MeshTri3);
        end
        objs(2) = [];
    end
end

blender.MeshGroup = objs;

disp(['begin to save surface mesh']);
savejson('', blender, 'FileName', bpmwpath('surfacemesh.jmsh'), 'ArrayIndent', 0);
