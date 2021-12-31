function nodedata=surf2jmesh(filename)

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
