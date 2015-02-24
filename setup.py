import platform
import sys
from datetime import date
import os
from config import get_version
from jmxfetch import JMX_FETCH_JAR_NAME

try:
    from setuptools import setup, find_packages

    # required to build the cython extensions
    from distutils.extension import Extension #pylint: disable=no-name-in-module

except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

# Extra arguments to pass to the setup function
extra_args = {}

# Prereqs of the build. Won't get installed when deploying the egg.
setup_requires = [
]

# Prereqs of the install. Will install when deploying the egg.
install_requires=[
]

# Modified on mac
app_name = 'datadog-agent'
# plist (used only on mac)
plist = None

if sys.platform == 'win32':
    from glob import glob
    import py2exe
    import pysnmp_mibs
    import pyVim
    import pyVmomi
    install_requires.extend([
        'adodbapi==2.6.0.7',
        'elementtree==1.2.7.20070827-preview',
        'httplib2==0.9',
        'pg8000==1.10.1',
        'psutil==2.1.3',
        'pycurl==7.19.5',
        'pymongo==2.7.2',
        'pymysql==0.6.2',
        'pysnmp-mibs==0.1.4',
        'pysnmp==4.2.5',
        'python-memcached==1.53',
        'pyvmomi==5.5.0.2014.1.1',
        'pywin32==217',
        'redis==2.10.3',
        'requests==2.4.3',
        'simplejson==3.6.4',
        'tornado==3.2.2',
        'wmi==1.4.9',
    ])

    # Modules to force-include in the exe
    include_modules = [
        # 3p
        'win32service',
        'win32serviceutil',
        'win32event',
        'simplejson',
        'adodbapi',
        'elementtree.ElementTree',
        'pycurl',
        'tornado.curl_httpclient',
        'pymongo',
        'pymysql',
        'psutil',
        'pg8000',
        'redis',
        'requests',
        'pysnmp',
        'pysnmp.smi.mibs.*',
        'pysnmp.smi.mibs.instances.*',
        'pysnmp_mibs.*',
        'pysnmp.entity.rfc3413.oneliner.*',
        'pyVim.*',
        'pyVmomi.*',

        # agent
        'checks.network_checks',
        'checks.libs.vmware.*',
        'httplib2',

        # pup
        'tornado.websocket',
        'tornado.web',
        'tornado.ioloop',
    ]

    class Target(object):
        def __init__(self, **kw):
            self.__dict__.update(kw)
            self.version = get_version()
            self.company_name = 'Datadog, Inc.'
            self.copyright = 'Copyright 2013 Datadog, Inc.'
            self.cmdline_style = 'pywin32'

    agent_svc = Target(name='Datadog Agent', modules='win32.agent', dest_base='ddagent')

    extra_args = {
        'options': {
            'py2exe': {
                'includes': ','.join(include_modules),
                'optimize': 0,
                'compressed': True,
                'bundle_files': 3,
                'excludes': ['numpy'],
                'dll_excludes': [ "IPHLPAPI.DLL", "NSI.dll",  "WINNSI.DLL",  "WTSAPI32.dll"],
                'ascii':False,
            },
        },
        'console': ['win32\shell.py'],
        'service': [agent_svc],
        'windows': [{'script': 'win32\gui.py',
                     'dest_base': "agent-manager",
                     'uac_info': "requireAdministrator", # The manager needs to be administrator to stop/start the service
                     'icon_resources': [(1, r"packaging\datadog-agent\win32\install_files\dd_agent_win_256.ico")],
                     }],
        'data_files': [
            ("Microsoft.VC90.CRT", glob(r'C:\Python27\redist\*.*')),
            ('jmxfetch', [r'checks\libs\%s' % JMX_FETCH_JAR_NAME]),
            ('gohai', [r'gohai\gohai.exe'])
        ],
    }

elif sys.platform == 'darwin':
    app_name = 'Datadog Agent'

    from plistlib import Plist
    plist = Plist.fromFile(os.path.dirname(os.path.realpath(__file__)) + '/packaging/Info.plist')
    plist.update(dict(
        CFBundleGetInfoString="{0}, Copyright (c) 2009-{1}, Datadog Inc.".format(get_version(), date.today().year),
        CFBundleVersion=get_version()
    ))

    extra_args = {
        'app': ['gui.py'],
        'data_files': ['status.html', 'datadog-cert.pem', 'checks', 'checks.d', 'images', 'dogstream'],
        'options': {
            'py2app': {
                'optimize': 0,
                'iconfile': 'packaging/Agent.icns',
                'packages': ['requests', 'supervisor', 'tornado'],
                'extra_scripts': ['agent.py', 'ddagent.py', 'dogstatsd.py', 'supervisord.py', 'supervisorctl.py'],
                'plist': plist
            }
        }
    }


setup(
    name=app_name,
    version=get_version(),
    description="DevOps' best friend",
    author='DataDog',
    author_email='dev@datadoghq.com',
    url='http://www.datadoghq.com',
    install_requires=install_requires,
    setup_requires=setup_requires,
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    test_suite='nose.collector',
    zip_safe=False,
    **extra_args
)
