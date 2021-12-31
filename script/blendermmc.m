function blendermmc(paramfile, meshfile)

param=loadjson(paramfile);
meshdata=load(meshfile));

%% Pre-processing data
propbk = [0,0,1,1];
prop = [propbk;reshape(param.prop,[],max(meshdata.elem(:,5)))'];
Q=num2cell(param.srcdir);
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
cfg.srcpos=param.srcpos;
cfg.srcdir= dir';
cfg.prop= prop;
cfg.tstart=0;
cfg.tend=5e-9;
cfg.tstep=5e-9;
cfg.debuglevel='TP';
cfg.issaveref=0;
cfg.method='elem';
cfg.e0 = '-';

save('-mat7-binary',bpmwpath('mmccfg.mat'),'cfg');

%% run the simulation

flux=mmclab(cfg);

%% Post-processing simulation result

fluxlog1 = log10(abs(flux.data(1:size(cfg.node,1))));
min = unique(fluxlog1);
fluxlog=fluxlog1;
fluxlog(isinf(fluxlog1)) = min(2);


savejson('',struct('logflux',fluxlog(:)'),'FileName',bpmwpath('mmcoutput.json'),'ArrayIndent',0);

