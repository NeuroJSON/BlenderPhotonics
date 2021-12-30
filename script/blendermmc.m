function blendermmc(paramfile, meshfile)

param=loadjson(paramfile)
meshdata=load(meshfile);

%% Pre-processing data
propbk = [0,0,1,1];
prop = [propbk;param.prop];
Q=num2cell(param.cfg.srcdir);
[w,x,y,z] = Q{:};
R = [1-2*y^2-2*z^2,2*x*y-2*z*w,2*x*z+2*y*w;
    2*x*y+2*z*w,1-2*x^2-2*z^2,2*y*z-2*x*w;
    2*x*z-2*y*w,2*y*z+2*x*w,1-2*x^2-2*y^2];
dir = R*[0;0;-1];

%% cfg build
cfg.nphoton= double(param.cfg.nphoton);
cfg.srctype=param.cfg.srctype;
cfg.srcpos=param.cfg.srcpos;
cfg.srcdir= dir';
cfg.srcparam1=param.cfg.srcparam1;
cfg.srcparam2=param.cfg.srcparam2;
cfg.prop= prop;
cfg.node = meshdata.node;
cfg.elem = meshdata.elem(:,1:4);
cfg.elemprop=meshdata.elem(:,5);
cfg.tstart=0;
cfg.tend=param.cfg.tend;
cfg.tstep=param.cfg.tstep;
cfg.isreflect=double(param.cfg.isreflect);
cfg.isnormalized=param.cfg.isnormalized;
cfg.gpuid=param.cfg.gpuid;
cfg.unitinmm = param.cfg.unitinmm;
cfg.outputtype=param.cfg.outputtype;
cfg.debuglevel=param.cfg.debuglevel;
cfg.method=param.cfg.method;

if(strcmp(cfg.srctype,'pencil') || strcmp(cfg.srctype,'isotropic') || strcmp(cfg.srctype,'cone'))
    cfg.e0=tsearchn(cfg.node,cfg.elem,cfg.srcpos);
    if(strcmp(cfg.srctype,'pencil') && isnan(cfg.e0))
        cfg.e0 = '-';
    end
else
    srcdef=struct('srctype',cfg.srctype,'srcpos',cfg.srcpos,'srcdir',cfg.srcdir,...
         'srcparam1',cfg.srcparam1,'srcparam2',cfg.srcparam2);
    [cfg.node,cfg.elem] = mmcaddsrc(cfg.node,[cfg.elem cfg.elemprop],...
          mmcsrcdomain(srcdef,[min(cfg.node);max(cfg.node)]));
end

save(bpmwpath('mmccfg.mat'),'cfg');

%% run the simulation

%cfg=mmclab(cfg,'prep');

flux=mmclab(cfg);

%% Post-processing simulation result

fluxlog1 = log10(abs(flux.data(1:size(cfg.node,1))));
min = unique(fluxlog1);
fluxlog=fluxlog1;
fluxlog(isinf(fluxlog1)) = min(2);


savejson('',struct('logflux',fluxlog(:)'),'FileName',bpmwpath('mmcoutput.json'),'ArrayIndent',0);

