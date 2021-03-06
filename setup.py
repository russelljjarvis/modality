import sys
from modality import __version__
from distutils.core import setup

modality_data = ['data/gammaval.pkl']

if 'install' in sys.argv:
    try:
        from src import write_qDiptab
        write_qDiptab.main()
        modality_data += ['data/qDiptab.csv']
    except Exception as e:
        print("Tabulated p-values for Hartigan's diptest not loaded due to "
              "error:\n\t {}.\n This means that p-values for Hartigan's "
              "(uncalibrated) diptest cannot be computed. Loading tabulated "
              "p-values requires the R package 'diptest' as well as the "
              "python module rpy2.".format(e))

setup(name='modality',
      version=__version__,
      description='Non-parametric tests for unimodality',
      author='Kerstin Johnsson',
      author_email='kerstin.johnsson@hotmail.com',
      url='https://github.com/kjohnsson/modality',
      license='MIT',
      packages=['modality', 'modality.calibration', 'modality.util'],
      package_data={'modality': modality_data,
                    'modality.calibration': ['data/*.pkl']})
