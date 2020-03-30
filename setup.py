import glob
from setuptools import setup, find_packages

'''
with open('README.md') as f:
    readme = f.read()
'''

'''
with open('LICENSE') as f:
    license = f.read()
'''

setup(
    name='ansible-dev-tools',
    version='0.1.1',
    description='various tools for debuggers of ansible',
    author='James Tanner',
    author_email='tanner.jc@gmail.com',
    url='https://github.com/jctanner/ansible-dev-tools',
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
