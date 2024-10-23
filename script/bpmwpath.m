function tempname = bpmwpath(fname)
%
% tempname=bpmwpath(fname)
%
% return the full path of a file name by prepending the BlenderPhotonics temporary folder
%
% author: Qianqian Fang (q.fang at neu.edu)
%
% input:
%    fname: a temporary file used internally by BP
%
% output:
%    tempname: the full path of the temporary file in the BP workfolder
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

if (nargin < 1) || isempty(fname)
    fname = '';
end

tdir = mwpath('blenderphotonics');
if (exist(tdir) == 0)
    mkdir(tdir);
end
tempname = [tdir filesep fname];
