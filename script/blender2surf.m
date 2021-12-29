function blender2surf

blender=loadjson(bpmwpath('blendersurf.jmsh'), 'FastArrayParser',0);

objs=blender.BlenderObject;
if(~isempty(regexp(blender.param.action,'repair')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshPoly))
            [objs{i}.MeshNode, objs{i}.MeshPoly]=meshcheckrepair(objs{i}.MeshNode, objs{i}.MeshPoly, 'meshfix');
        end
    end
end

if(~isempty(regexp(blender.param.action,'smooth')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshPoly))
            objs{i}.MeshNode=sms(objs{i}.MeshNode, objs{i}.MeshPoly, str2double(blender.param.actionlevel));
        end
    end
end

if(~isempty(regexp(blender.param.action,'reorient')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshPoly))
            [objs{i}.MeshNode, objs{i}.MeshPoly]=surfreorient(objs{i}.MeshNode, objs{i}.MeshPoly);
        end
    end
end

if(~isempty(regexp(blender.param.action,'simplify')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshPoly))
            [objs{i}.MeshNode, objs{i}.MeshPoly]=meshresample(objs{i}.MeshNode, objs{i}.MeshPoly, str2double(blender.param.actionlevel));
        end
    end
end

if(~isempty(regexp(blender.param.action,'boolean')))
    if(length(objs)==2)
        [node, face]=surfboolean(objs{1}.MeshNode, objs{1}.MeshPoly, blender.param.actionlevel, objs{2}.MeshNode, objs{2}.MeshPoly);
        objs=struct('MeshNode',node, 'MeshPoly', face);
    end
end

blender.BlenderObject=objs;

disp(['begin to save surface mesh'])
savejson('',blender,'FileName',bpmwpath('surfacemesh.jmsh'),'ArrayIndent',0);
