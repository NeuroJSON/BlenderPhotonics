function tempname=bpmwpath(fname)
if (nargin < 1) || isempty(fname)
    fname = '';
end

tdir=mwpath('blenderphotonics')
if(exist(tdir)==0)
    mkdir(tdir)
end
tempname=[tdir filesep fname];
