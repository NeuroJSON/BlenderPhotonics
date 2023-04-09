class BlenderPhotonicsError(Exception):
    pass


class BlenderPhotonicsDependencyError(BlenderPhotonicsError):
    """Errors concerning missing system or Python utilities/modules/packages"""
    def __init__(self, dep: str, *args, **kwargs):
        self.missing_dep = dep
        super().__init__(f'Required dependency not found: {dep}', *args)


class BlenderPhotonicsMeshingError(BlenderPhotonicsError):
    """Meshing failure, typically a forwarding of some backend error"""
    pass
