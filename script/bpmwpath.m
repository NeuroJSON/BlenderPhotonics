function tempname=bpmwpath(fname)
%
% tempname=bpmwpath(fname)
%
% return the full path of a file name by prepending the BlenderPhotonics temporary folder
%
% author: Qianqian Fang (q.fang at neu.edu)
%
% input:
%	 fname: a temporary file used internally by BP
%
% output:
%	 tempname: the full path of the temporary file in the BP workfolder 
%
% license: GPLv3 or later, see LICENSE.txt for details
%
% reference: 
% @article {BlenderPhotonics2022,
%  author = {Zhang, Yuxuang and Fang, Qianqian},
%  title = {{BlenderPhotonics -- a versatile environment for 3-D complex bio-tissue modeling and light transport simulations based on Blender}},
%  elocation-id = {2022.01.12.476124},
%  year = {2022},
%  doi = {10.1101/2022.01.12.476124},
%  publisher = {Cold Spring Harbor Laboratory},
%  URL = {https://www.biorxiv.org/content/early/2022/01/14/2022.01.12.476124},
%  eprint = {https://www.biorxiv.org/content/early/2022/01/14/2022.01.12.476124.full.pdf},
%  journal = {bioRxiv}
% }
%
% -- this function is part of BlenderPhotonics (http://mcx.space/bp)
%

if (nargin < 1) || isempty(fname)
    fname = '';
end

tdir=mwpath('blenderphotonics')
if(exist(tdir)==0)
    mkdir(tdir)
end
tempname=[tdir filesep fname];
