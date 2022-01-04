function blendermmc(paramfile, meshfile)

param=loadjson(paramfile);
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
cfg.gpuid=-1;
cfg.unitinmm = param.cfg.unitinmm;
cfg.node = meshdata.node;
cfg.elem = meshdata.elem(:,1:4);
cfg.elemprop=meshdata.elem(:,5);
cfg.srcpos=param.cfg.srcpos;
cfg.srcdir= dir';
cfg.prop= prop;
cfg.tstart=0;
cfg.tend=param.cfg.tend;
cfg.tstep=param.cfg.tstep;
cfg.debuglevel=param.cfg.debuglevel;
cfg.issaveref=0;
cfg.method=param.cfg.method;
cfg.isreflect=uint8(param.cfg.isreflect);
cfg.isnormalized=param.cfg.isnormalized;
cfg.gpuid=param.cfg.gpuid;

cfg.e0=tsearchn(cfg.node,cfg.elem,cfg.srcpos);
if(isnan(cfg.e0))
    cfg.e0 = '-';
end

save('-mat7-binary',bpmwpath('mmccfg.mat'),'cfg');

%% run the simulation

flux=mmclab(cfg);

%% Post-processing simulation result

fluxlog1 = log10(abs(flux.data(1:size(cfg.node,1))));
min = unique(fluxlog1);
fluxlog=fluxlog1;
fluxlog(isinf(fluxlog1)) = min(2);


savejson('',struct('logflux',fluxlog(:)'),'FileName',bpmwpath('mmcoutput.json'),'ArrayIndent',0);

