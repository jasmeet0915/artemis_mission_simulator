import os
from setuptools import setup, find_packages

package_name = 'lunar_terrain_exporter'


def collect_data_files(source_dir, install_prefix):
    """Walk a directory tree and return (install_dir, [files]) tuples."""
    data_files = []
    for root, _dirs, files in os.walk(source_dir):
        if files:
            install_dir = os.path.join(install_prefix, root)
            file_paths = [os.path.join(root, f) for f in files]
            data_files.append((install_dir, file_paths))
    return data_files


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config',
            ['config/artemis_sites.yaml']),
        ('share/' + package_name + '/environment',
            ['hooks/' + package_name + '.dsv',
             'hooks/' + package_name + '.sh']),
    ] + collect_data_files('models', 'share/' + package_name),
    install_requires=['setuptools'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'lunar_terrain_exporter = lunar_terrain_exporter.lunar_terrain_exporter:LunarTerrainExporter.from_cli',
        ],
    },
)
