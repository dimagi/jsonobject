from setuptools import setup

from setuptools.extension import Extension

try:
    # Only use Cython if it's installed in the environment, otherwise use the provided C
    import Cython  # noqa: F401
    USE_CYTHON = True
except ImportError:
    USE_CYTHON = False

ext = '.pyx' if USE_CYTHON else '.c'
extensions = [
    Extension('jsonobject.api', ["jsonobject/api" + ext],),
    Extension('jsonobject.base', ["jsonobject/base" + ext],),
    Extension('jsonobject.base_properties', ["jsonobject/base_properties" + ext],),
    Extension('jsonobject.containers', ["jsonobject/containers" + ext],),
    Extension('jsonobject.properties', ["jsonobject/properties" + ext],),
    Extension('jsonobject.utils', ["jsonobject/utils" + ext],),
]

if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions, compiler_directives={"language_level" : "3str"})
else:
    print("You are running without Cython installed. It is highly recommended to run\n"
          "  ./scripts/install_cython.sh\n"
          "before you continue")

setup(
    name='jsonobject',
    ext_modules=extensions,
)
