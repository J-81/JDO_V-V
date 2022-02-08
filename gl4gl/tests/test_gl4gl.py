""" A small set of tests related to all submodules, mostly import checks """


def test_imports():
    from gl4gl import VnV

    dir(VnV)

    from gl4gl import StageThis

    dir(StageThis)

    from gl4gl import PathAnnotate

    dir(PathAnnotate)

    from gl4gl import PostProcessing

    dir(PostProcessing)
