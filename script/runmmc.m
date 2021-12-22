%% load the sample data
clear all
load MMCinfo.mat
load meshdata.mat

%% Pre-processing data
airpara = [0,0,1,1];
Optical_parameter = [airpara;reshape(Optical,[],max(elem(:,5)))'];
Q=num2cell(light_direction);
[w,x,y,z] = Q{:};
R = [1-2*y^2-2*z^2,2*x*y-2*z*w,2*x*z+2*y*w;
    2*x*y+2*z*w,1-2*x^2-2*z^2,2*y*z-2*x*w;
    2*x*z-2*y*w,2*y*z+2*x*w,1-2*x^2-2*y^2];
dir = R*[0;0;-1];

%% cfg build
cfg.nphoton= double(light_info(1));
cfg.gpuid=-1;
cfg.unitinmm = light_info(3);
cfg.node = node;
cfg.elem = elem(:,1:4);
cfg.elemprop=elem(:,5);
cfg.srcpos=light_location;
cfg.srcdir= dir';
cfg.prop= Optical_parameter;
cfg.tstart=0;
cfg.tend=5e-9;
cfg.tstep=5e-9;
cfg.debuglevel='TP';
cfg.issaveref=1;  % in addition to volumetric fluence, also save surface diffuse reflectance
cfg.method='elem';
cfg.e0 = '-';

%% run the simulation

flux=mmclab(cfg);

%% Post-processing simulation result

fluxlog1 = log10(abs(flux.data(1:size(cfg.node,1))));
min = unique(fluxlog1);
fluxlog=fluxlog1;
fluxlog(find(fluxlog1 == -inf)) = min(2);
save('-mat7-binary','fluxlog.mat','fluxlog'); % flux to log scale and -inf to 0

faces = meshface(cfg.elem);
order = faces';
order = order(:);
[~,i,~] = unique(order,'first');
nodeorder = order(sort(i));
% get vetexs order for blender(.stl file to blender will change the order for vertex. If you use .off file can avoid this step. However, you need install .off import add-on first and change the import_mesh.stl to import_mesh.off)
% In Matlab, commond can be "nodeorder = unique(order,'stable');". Octave do not accept 'stable'

save('-mat7-binary','nodeorder.mat','nodeorder');
