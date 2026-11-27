# Copyright 2026 Jasmeet Singh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Tests for the CLI argument parsing and subcommands."""

from pathlib import Path
import tempfile

from lunar_terrain_exporter.cli import build_parser, load_sites_from_yaml
import pytest
import yaml


class TestSiteSubcommand:
    def test_site_full_roi(self):
        parser = build_parser()
        args = parser.parse_args([
            'site', 'connecting_ridge',
            '--output-dir', '/tmp/out',
        ])
        assert args.command == 'site'
        assert args.site_name == 'connecting_ridge'
        assert args.output_dir == '/tmp/out'
        assert args.lat is None
        assert args.lon is None

    def test_site_with_code(self):
        """CLI should accept a site code as well as a name."""
        parser = build_parser()
        args = parser.parse_args(['site', 'Site01'])
        assert args.site_name == 'Site01'

    def test_site_with_crop(self):
        parser = build_parser()
        args = parser.parse_args([
            'site', 'shackleton_rim',
            '--lat', '-86.5',
            '--lon', '-4.0',
            '--size', '5.0',
            '--output-dir', '/tmp/out',
        ])
        assert args.site_name == 'shackleton_rim'
        assert args.lat == -86.5
        assert args.size == 5.0

    def test_site_default_output_dir(self):
        parser = build_parser()
        args = parser.parse_args(['site', 'connecting_ridge'])
        assert args.output_dir == '.'

    def test_site_default_dimensions(self):
        parser = build_parser()
        args = parser.parse_args(['site', 'connecting_ridge'])
        assert args.size == 10.0


class TestBatchSubcommand:
    def test_batch_mode(self):
        parser = build_parser()
        args = parser.parse_args([
            'batch',
            '--config', 'sites.yaml',
            '--output-dir', '/tmp/out',
        ])
        assert args.command == 'batch'
        assert args.config == 'sites.yaml'
        assert args.output_dir == '/tmp/out'

    def test_batch_requires_config(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['batch', '--output-dir', '/tmp/out'])


class TestNoSubcommand:
    def test_no_command_gives_none(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


class TestLoadSitesFromYaml:
    def _write_yaml(self, data: dict, path: Path) -> Path:
        config_file = path / 'sites.yaml'
        with open(config_file, 'w') as f:
            yaml.dump(data, f)
        return config_file

    def test_load_single_site_with_bbox(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                'sites': [{
                    'site': 'connecting_ridge',
                    'roi': {
                        'use_full': False,
                        'bounding_box': {'lat': -86.5, 'lon': -4.0},
                    },
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 1
            assert sites[0].name == 'connecting_ridge'
            assert sites[0].site_code == 'Site01'
            assert sites[0].roi.bounding_box.size_km == 10.0

    def test_load_single_site_with_full_roi(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                'sites': [{
                    'site': 'connecting_ridge',
                    'roi': {'use_full': True},
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 1
            assert sites[0].name == 'connecting_ridge'
            assert sites[0].roi.use_full is True
            assert sites[0].roi.bounding_box is None
            assert 'Site01' in sites[0].dem_url

    def test_load_multiple_sites(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                'sites': [
                    {
                        'site': 'connecting_ridge',
                        'roi': {
                            'use_full': False,
                            'bounding_box': {'lat': -86.0, 'lon': 0.0},
                        },
                    },
                    {
                        'site': 'shackleton_rim',
                        'roi': {
                            'use_full': False,
                            'bounding_box': {
                                'lat': -87.0, 'lon': 10.0,
                                'size_km': 5.0,
                            },
                        },
                    },
                ]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 2
            assert sites[0].name == 'connecting_ridge'
            assert sites[1].roi.bounding_box.size_km == 5.0

    def test_missing_required_field_raises(self):
        """An entry without a 'site' key is skipped (warning printed)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                'sites': [{'name': 'bad'}]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert len(sites) == 0

    def test_load_site_with_bbox_checks_dem_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = self._write_yaml({
                'sites': [{
                    'site': 'shackleton_rim',
                    'roi': {
                        'use_full': False,
                        'bounding_box': {'lat': -86.5, 'lon': -4.0, 'size_km': 5.0},
                    },
                }]
            }, Path(tmpdir))
            sites = load_sites_from_yaml(config_file)
            assert sites[0].roi.bounding_box.size_km == 5.0
            assert 'Site04' in sites[0].dem_url
