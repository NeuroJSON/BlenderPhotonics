function blender2surf(filename)

blender=loadjson(filename, 'FastArrayParser',0);

objs=blender.MeshGroup;
if(~isempty(regexp(blender.param.action,'repair')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshSurf))
            [objs{i}.MeshNode, objs{i}.MeshSurf]=meshcheckrepair(objs{i}.MeshNode, objs{i}.MeshSurf, 'meshfix');
        end
    end
end

if(~isempty(regexp(blender.param.action,'smooth')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshSurf))
            objs{i}.MeshNode=sms(objs{i}.MeshNode, objs{i}.MeshSurf, blender.param.level);
        end
    end
end

if(~isempty(regexp(blender.param.action,'reorient')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshSurf))
            [objs{i}.MeshNode, objs{i}.MeshSurf]=surfreorient(objs{i}.MeshNode, objs{i}.MeshSurf);
        end
    end
end

if(~isempty(regexp(blender.param.action,'simplify')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshSurf))
            [objs{i}.MeshNode, objs{i}.MeshSurf]=meshresample(objs{i}.MeshNode, objs{i}.MeshSurf, blender.param.level);
        end
    end
end

if(~isempty(regexp(blender.param.action,'remesh')))
    for i=1:length(objs)
        if(~iscell(objs{i}.MeshSurf))
            [objs{i}.MeshNode, objs{i}.MeshSurf]=surfboolean(objs{i}.MeshNode, objs{i}.MeshSurf, 'remesh', objs{i}.MeshNode, objs{i}.MeshSurf);
        end
    end
end

op=regexp(blender.param.action,'boolean-[a-zA-Z]+','match')
if(~isempty(op))
    if(length(objs)==2)
        if(blender.param.level>=0)
             [objs{1}.MeshNode, objs{1}.MeshSurf]=surfboolean(objs{1}.MeshNode, objs{1}.MeshSurf, regexprep(op{1},'boolean-',''), objs{2}.MeshNode, objs{2}.MeshSurf);
        else
             [objs{1}.MeshNode, objs{1}.MeshSurf]=surfboolean(objs{2}.MeshNode, objs{2}.MeshSurf, regexprep(op{1},'boolean-',''), objs{1}.MeshNode, objs{1}.MeshSurf);
        end
        objs{2}=[];
    end
end

blender.MeshGroup=objs;

disp(['begin to save surface mesh'])
savejson('',blender,'FileName',bpmwpath('surfacemesh.jmsh'),'ArrayIndent',0);
