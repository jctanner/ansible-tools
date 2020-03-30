import glob
from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()


with open('LICENSE') as f:
    license = f.read()


setup(
    name='ansible-dev-tools',
    version='0.1.0',
    description='various tools for debuggers of ansible',
    long_description=readme,
    author='James Tanner',
    author_email='tanner.jc@gmail.com',
    url='https://github.com/jctanner/ansible-dev-tools',
    license=license,
    packages=find_packages(),
    scripts=[x for x in glob.glob('scripts/*') if not '__pycache__' in x],
    python_requires='>=2.7',
    install_reqs=[
        'beautifulsoup4',
        'epdb',
        'logzero',
        'packaging',
        'requests',
        'sh'
    ]
 )
