#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_cli
----------------------------------

Tests for `histonets_cv.cli` module.
"""
import base64
import io
import json
import os
import tempfile
import unittest

import cv2
import networkx as nx
import numpy as np
from click.testing import CliRunner

from histonets_cv import cli, utils


def fixtures_path(file):
    return os.path.abspath(os.path.join('tests', 'fixtures', file))


def encode_base64(file_path):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode()


def decode_base64(base64_string):
    return utils.Image(
        base64.b64decode(utils.local_encode(base64_string))
    ).image


def edgeset(graph):
    # We remove property id since it is not consistent in GEXF format
    return set([
        tuple(
            sorted([u, v])
            + sorted((k, v) for k, v in props.items() if k != 'id'))
        for u, v, props in graph.edges(data=True)
    ])


def nodeset(graph):
    return sorted(graph.nodes(data=True))


class TestHistonetsCli(unittest.TestCase):
    def setUp(self):
        self.image_url = 'http://httpbin.org/image/jpeg'
        self.image_file = 'file://' + fixtures_path('test.png')
        self.image_404 = 'file:///not_found.png'
        self.image_jpg = fixtures_path('test.jpg')
        self.image_png = fixtures_path('test.png')
        self.image_b64 = fixtures_path('test.b64')
        self.image_5050_b64 = fixtures_path('test_5050.b64')
        self.image_template = 'file://' + fixtures_path('template.png')
        self.image_template_h = 'file://' + fixtures_path('template_h.png')
        self.image_template_v = 'file://' + fixtures_path('template_v.png')
        self.image_template_b = 'file://' + fixtures_path('template_b.png')
        self.image_template_m = 'file://' + fixtures_path('template_m.png')
        self.image_posterized = 'file://' + fixtures_path('poster_kmeans4.png')
        self.image_map = 'file://' + fixtures_path('map.png')
        self.image_map_ridges = ('file://'
                                 + fixtures_path('map_ridges_invert.png'))
        self.image_grid = fixtures_path('grid.png')
        self.tmp_jpg = os.path.join(tempfile.gettempdir(), 'test.jpg')
        self.tmp_png = os.path.join(tempfile.gettempdir(), 'test.png')
        self.tmp_tiff = os.path.join(tempfile.gettempdir(), 'test.tiff')
        self.tmp_no_format = os.path.join(tempfile.gettempdir(), 'test')
        self.tmp_invalid_format = os.path.join(tempfile.gettempdir(), 'test.a')
        self.runner = CliRunner()

    def tearDown(self):
        pass

    def test_command_line_interface(self):
        result = self.runner.invoke(cli.main)
        assert result.exit_code == 0
        help_result = self.runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help' in help_result.output
        assert 'Show this message and exit.' in help_result.output
        assert '--version' in help_result.output
        assert 'Show the version and exit.' in help_result.output
        assert 'Download IMAGE.' in result.output

    def test_rst_option(self):
        result = self.runner.invoke(cli.main)
        assert result.exit_code == 0
        help_result = self.runner.invoke(cli.main, ['--rst'])
        assert help_result.exit_code == 0
        assert '~' in help_result.output
        assert 'Commands' in help_result.output
        assert 'Options' in help_result.output

    def test_download_command_image_file(self):
        result = self.runner.invoke(cli.download, [self.image_file])
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 1

    def test_download_command_image_url(self):
        result = self.runner.invoke(cli.download, [self.image_url])
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 1

    def test_download_command_image_not_found(self):
        result = self.runner.invoke(cli.download, [self.image_404])
        assert 'Error' in result.output

    def test_download_command_help(self):
        result = self.runner.invoke(cli.download, ['--help'])
        assert 'Download IMAGE.' in result.output

    def test_io_handler_to_file_as_jpg(self):
        result = self.runner.invoke(
            cli.download,
            [self.image_file, '--output', self.tmp_jpg]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_jpg = cv2.imread(self.image_jpg)
        tmp_jpg = cv2.imread(self.tmp_jpg)
        assert np.array_equal(image_jpg, tmp_jpg)

    def test_io_handler_to_file_as_png(self):
        result = self.runner.invoke(
            cli.download,
            [self.image_file, '--output', self.tmp_png]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_png = cv2.imread(self.image_png)
        tmp_png = cv2.imread(self.tmp_png)
        assert np.array_equal(image_png, tmp_png)

    def test_io_handler_to_file_and_convert_to_tiff(self):
        result = self.runner.invoke(
            cli.download,
            [self.image_file, '--output', self.tmp_tiff]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_png = cv2.imread(self.image_png)
        tmp_tiff = cv2.imread(self.tmp_tiff)
        assert np.array_equal(image_png, tmp_tiff)

    def test_io_handler_to_file_with_no_format(self):
        result = self.runner.invoke(
            cli.download,
            [self.image_file, '--output', self.tmp_no_format]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_png = cv2.imread(self.image_png)
        tmp_no_format = cv2.imread(self.tmp_no_format)
        assert np.array_equal(image_png, tmp_no_format)

    def test_io_handler_to_file_with_invalid_format(self):
        result = self.runner.invoke(
            cli.download,
            [self.image_file, '--output', self.tmp_invalid_format]
        )
        assert 'Error' in result.output
        assert len(result.output.strip()) > 0

    def test_io_handler_to_stdout(self):
        result = self.runner.invoke(cli.download, [self.image_file])
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 0
        with io.open(self.image_b64) as image_b64:
            assert result.output == image_b64.read()

    def test_contrast_invalid_value(self):
        result = self.runner.invoke(cli.contrast, ['250', self.image_file])
        assert 'Invalid value for "value"' in result.output

    def test_contrast_integer(self):
        test_contrast_image = encode_base64(
            fixtures_path('test_low_contrast.png')
        )
        result = self.runner.invoke(cli.contrast, ['50', self.image_file])
        assert test_contrast_image == result.output.rstrip()

    def test_brightness_invalid_value(self):
        result = self.runner.invoke(cli.brightness, ['250', self.image_file])
        assert 'Invalid value for "value"' in result.output

    def test_brightness_integer(self):
        test_brightness_image = encode_base64(
            fixtures_path('test_brightness_darken.png')
        )
        result = self.runner.invoke(cli.brightness, ['50', self.image_file])
        assert test_brightness_image == result.output.rstrip()

    def test_smooth_invalid_value(self):
        result = self.runner.invoke(cli.smooth, ['101', self.image_file])
        assert 'Invalid value for "value"' in result.output

    def test_smooth_integer(self):
        test_smooth_image = encode_base64(
            fixtures_path('smooth50.png')
        )
        result = self.runner.invoke(cli.smooth, ['50', self.image_file])
        assert test_smooth_image == result.output.rstrip()

    def test_histogram_equalization_invalid_value(self):
        result = self.runner.invoke(cli.equalize, ['150', self.image_file])
        assert 'Invalid value for "value"' in result.output

    def test_histogram_equalization_integer(self):
        test_hist_image = encode_base64(
            fixtures_path('test_hist_eq5.png')
        )
        result = self.runner.invoke(cli.equalize, ['50', self.image_file])
        assert test_hist_image == result.output.rstrip()

    def test_denoise_invalid_value(self):
        result = self.runner.invoke(cli.denoise, ['110', self.image_file])
        assert 'Invalid value for "value"' in result.output

    def test_denoise_integer(self):
        test_denoise_image = encode_base64(
            fixtures_path('denoised10.png')
        )
        result = self.runner.invoke(cli.denoise, ['10', self.image_file])
        assert test_denoise_image == result.output.rstrip()

    def test_command_pipeline(self):
        actions = json.dumps([
            {'action': 'brightness', 'options': {'value': 150}},
            {'action': 'contrast', 'options': {'value': 150}}
        ])
        result = self.runner.invoke(cli.pipeline, [actions, self.image_file])
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 0
        with io.open(self.image_5050_b64) as image_b64:
            assert result.output == image_b64.read()

    def test_command_pipeline_all_actions(self):
        actions = json.dumps([
            {"action": "denoise", "options": {"value": 9}},
            {"action": "equalize", "options": {"value": 10}},
            {"action": "brightness", "options": {"value": 122}},
            {"action": "contrast", "options": {"value": 122}},
            {"action": "smooth", "options": {"value": 12}},
            {"action": "posterize", "options":
                {"colors": 4, "method": "linear"}}
        ])
        result = self.runner.invoke(cli.pipeline, [actions, self.image_file])
        assert 'Error' not in result.output
        test_pipeline_full = encode_base64(
            fixtures_path('test_full_pipeline.png')
        )
        assert test_pipeline_full == result.output.strip()

    def test_command_pipeline_invalid(self):
        actions = json.dumps([
            {'action': 'command not found', 'options': {'value': 50}},
        ])
        result = self.runner.invoke(cli.pipeline, [actions, self.image_file])
        assert 'Error' in result.output
        assert len(result.output.strip()) > 0

    def test_command_pipeline_reraise_error(self):
        actions = json.dumps([
            {"action": "posterize", "options":
                {"value": 4, "method": "linear"}}
        ])
        result = self.runner.invoke(cli.pipeline, [actions, self.image_file])
        assert 'Error' in result.output
        assert not isinstance(result.exception, TypeError)
        assert len(result.output.strip()) > 0

    def test_command_posterize_linear(self):
        result = self.runner.invoke(
            cli.posterize,
            ['4', '-m', 'linear', self.image_file]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 0
        test_posterize_image = encode_base64(
            fixtures_path('poster_linear4.png')
        )
        assert test_posterize_image == result.output.strip()

    def test_command_posterize_linear_with_palette(self):
        palette = [
            [241, 238, 255],
            [27, 9, 0],
            [245, 128, 35],
            [91, 123, 164],
        ]
        result = self.runner.invoke(
            cli.posterize,
            ['4', '-m', 'linear', '-p', json.dumps(palette), self.image_file]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 0
        test_posterize_image = encode_base64(
            fixtures_path('poster_linear4.png')
        )
        assert test_posterize_image == result.output.strip()

    def test_command_posterize_default_method(self):
        result = self.runner.invoke(
            cli.posterize,
            ['4', self.image_file]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 0
        test_posterize_image = encode_base64(
            fixtures_path('poster_linear4.png')
        )
        assert test_posterize_image != result.output.strip()

    def test_command_clean(self):
        result = self.runner.invoke(cli.clean, [self.image_file])
        assert 'Error' not in result.output
        assert len(result.output.strip()) > 0
        test_clean = encode_base64(fixtures_path('clean.png'))
        image = encode_base64(self.image_png)
        assert abs(np.ceil(len(result.output.strip()) / 1e5)
                   - np.ceil(len(test_clean) / 1e5)) <= 2
        assert len(test_clean) < len(image)
        assert len(result.output.strip()) < len(image)

    def test_command_clean_section_with_palette(self):
        image_path = fixtures_path('icon.png')
        image = cv2.imread(image_path)
        palette = utils.get_palette(image[:, :, ::-1], n_colors=2)
        clean_image_b64 = self.runner.invoke(
            cli.clean,
            [image_path, '-c', 2, '-f', 100, '-p',
             json.dumps(palette.tolist())]
        ).output.strip()
        clean_image = decode_base64(clean_image_b64)
        section_path = fixtures_path('icon_section.png')
        section = cv2.imread(section_path)
        clean_section_b64 = self.runner.invoke(
            cli.clean,
            [section_path, '-c', 2, '-f', 100, '-p',
             json.dumps(palette.tolist())]
        ).output.strip()
        clean_section = decode_base64(clean_image_b64)
        clean_image_colors = sorted(utils.get_color_histogram(
            clean_image[:, :, ::-1]).keys())
        section_colors = sorted(utils.get_color_histogram(
            section[:, :, ::-1]).keys())
        clean_section_colors = sorted(utils.get_color_histogram(
            clean_section[:, :, ::-1]).keys())
        assert 'Error' not in clean_image_b64
        assert 'Error' not in clean_section_b64
        assert section_colors != clean_section_colors
        assert clean_section_colors == clean_image_colors

    def test_command_enhance_with_palette(self):
        image_path = fixtures_path('icon.png')
        image = cv2.imread(image_path)
        palette = utils.get_palette(image[:, :, ::-1], n_colors=8)
        result = self.runner.invoke(
            cli.enhance,
            [image_path, '-p', json.dumps(palette.tolist())]
        ).output.strip()
        assert 'Error' not in result
        assert len(result) > 0

    def test_command_enhance(self):
        result_clean = self.runner.invoke(cli.clean, [self.image_file])
        result_enhance = self.runner.invoke(cli.enhance, [self.image_file])
        assert abs(np.ceil(len(result_clean.output) / 1e5)
                   - np.ceil(len(result_enhance.output) / 1e5)) <= 2

    def test_command_match(self):
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 95, self.image_file]
        )
        assert 'Error' not in result.output
        assert [[[259, 349], [329, 381]]] == json.loads(result.output)

    def test_command_match_default(self):
        result_default = self.runner.invoke(
            cli.match,
            [self.image_template, self.image_file]
        )
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 80, self.image_file]
        )
        assert 'Error' not in result.output
        assert 'Error' not in result_default.output
        assert result_default.output == result.output

    def test_command_match_invalid(self):
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 95, '-th', 80, self.image_file]
        )
        assert 'Error' in result.output

    def test_command_match_flip_horizontally(self):
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 95, self.image_file]
        )
        assert 'Error' not in result.output
        result_h = self.runner.invoke(
            cli.match,
            [self.image_template_h, '-th', 95, '-f', 'h', self.image_file]
        )
        assert 'Error' not in result_h.output
        assert result.output == result_h.output

    def test_command_match_flip_vertically(self):
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 95, self.image_file]
        )
        assert 'Error' not in result.output
        result_v = self.runner.invoke(
            cli.match,
            [self.image_template_v, '-th', 95, '-f', 'v', self.image_file]
        )
        assert 'Error' not in result_v.output
        assert result.output == result_v.output

    def test_command_match_flip_both(self):
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 95, self.image_file]
        )
        assert 'Error' not in result.output
        result_b = self.runner.invoke(
            cli.match,
            [self.image_template_b, '-th', 95, '-f', 'b', self.image_file]
        )
        assert 'Error' not in result_b.output
        assert result.output == result_b.output

    def test_command_match_mask(self):
        exclude = [
            [[0, 0], [170, 0], [170, 50], [0, 50]],
            [[0, 50], [50, 50], [50, 82], [0, 82]],
            [[120, 50], [170, 50], [170, 82], [120, 82]],
            [[0, 82], [170, 82], [170, 132], [0, 132]],
        ]
        result = self.runner.invoke(
            cli.match,
            [self.image_template_m, '-th', 45,
             '-e', json.dumps(exclude), self.image_file]
        )
        test_matches = [[[209, 299], [379, 431]]]
        assert 'Error' not in result.output
        assert test_matches == json.loads(result.output)

    def test_command_match_mask_invalid(self):
        result = self.runner.invoke(
            cli.match,
            [self.image_template, '-th', 95,
             '-e', '[[[1,2],[5,7],[10,23,[2,3]]]', self.image_file]
        )
        assert 'Error' in result.output
        assert 'Polygon' in result.output

    def test_command_pipeline_match(self):
        exclude = [
            [[0, 0], [170, 0], [170, 50], [0, 50]],
            [[0, 50], [50, 50], [50, 82], [0, 82]],
            [[120, 50], [170, 50], [170, 82], [120, 82]],
            [[0, 82], [170, 82], [170, 132], [0, 132]],
        ]
        actions = json.dumps([
            {"action": "match", "options": {
                "templates": [self.image_template_m],
                "threshold": [45],
                "flip": ['both'],
                "exclude_regions": [exclude],
            }},
        ])
        result = self.runner.invoke(cli.pipeline, [actions, self.image_file])
        test_matches = [[[209, 299], [379, 431]]]
        assert 'Error' not in result.output
        assert test_matches == json.loads(result.output)

    def test_command_select_colors(self):
        result = self.runner.invoke(
            cli.select,
            [json.dumps((58, 36, 38)), '-t', 0,
             json.dumps((172, 99, 76)), '-t', 0,
             self.image_posterized]
        )
        masked = encode_base64(fixtures_path('masked_colors.png'))
        assert masked == result.output.strip()

    def test_command_select_colors_as_mask(self):
        result = self.runner.invoke(
            cli.select,
            [json.dumps((58, 36, 38)), '-t', 0,
             json.dumps((172, 99, 76)), '-t', 0,
             '--mask',
             self.image_posterized]
        )
        masked = encode_base64(fixtures_path('masked_bw.png'))
        assert masked == result.output.strip()

    def test_command_ridges(self):
        result = self.runner.invoke(
            cli.ridges,
            ['-w', 6, '-th', 160, '-d', 1,
             self.image_map]
        )
        masked = encode_base64(fixtures_path('map_noridge.png'))
        assert masked == result.output.strip()

    def test_command_ridges_as_mask(self):
        result = self.runner.invoke(
            cli.ridges,
            ['-w', 6, '-th', 160, '-d', 1, '-m',
             self.image_map]
        )
        mask = encode_base64(fixtures_path('map_ridge.png'))
        assert mask == result.output.strip()

    def test_command_blobs(self):
        result = self.runner.invoke(
            cli.blobs,
            ['-min', 0, '-max', 100,
             self.image_map_ridges],
        )
        masked = encode_base64(fixtures_path('map_noblobs8.png'))
        assert masked == result.output.strip()

    def test_command_blobs_4connected(self):
        result = self.runner.invoke(
            cli.blobs,
            ['-min', 0, '-max', 100, '-c', 4,
             self.image_map_ridges],
        )
        masked = encode_base64(fixtures_path('map_noblobs4.png'))
        assert masked == result.output.strip()

    def test_command_blobs_8connected(self):
        result = self.runner.invoke(
            cli.blobs,
            ['-min', 0, '-max', 100, '-c', 8,
             self.image_map_ridges],
        )
        masked = encode_base64(fixtures_path('map_noblobs8.png'))
        assert masked == result.output.strip()

    def test_command_blobs_antialiased(self):
        result = self.runner.invoke(
            cli.blobs,
            ['-min', 0, '-max', 100, '-c', 16,
             self.image_map_ridges],
        )
        masked = encode_base64(fixtures_path('map_noblobs_antialiased.png'))
        assert masked == result.output.strip()

    def test_binarize_default(self):
        result = self.runner.invoke(
            cli.binarize,
            [self.image_map],
        )
        binarized = encode_base64(fixtures_path('map_bw.png'))
        assert binarized == result.output.strip()

    def test_binarize_li(self):
        result = self.runner.invoke(
            cli.binarize,
            ['-m', 'li',
             self.image_map],
        )
        binarized = encode_base64(fixtures_path('map_bw.png'))
        assert binarized == result.output.strip()

    def test_binarize_otsu(self):
        result = self.runner.invoke(
            cli.binarize,
            ['-m', 'otsu',
             self.image_map],
        )
        binarized = encode_base64(fixtures_path('map_otsu.png'))
        assert binarized == result.output.strip()

    def test_dilate(self):
        result = self.runner.invoke(
            cli.dilate,
            [self.image_map],
        )
        dilated = encode_base64(fixtures_path('map_dilated_d1_i1.png'))
        assert dilated == result.output.strip()

    def test_dilate_default(self):
        result = self.runner.invoke(
            cli.dilate,
            ['-b', 'li', '-d', 1, '-p', 1,
             self.image_map],
        )
        dilated = encode_base64(fixtures_path('map_dilated_d1_i1.png'))
        assert dilated == result.output.strip()

    def test_dilate_invert(self):
        result = self.runner.invoke(
            cli.dilate,
            ['-d', 1, '-i',
             self.image_map],
        )
        dilated = encode_base64(fixtures_path('map_dilated_d1_invert.png'))
        assert dilated == result.output.strip()

    def test_skeletonize(self):
        result = self.runner.invoke(
            cli.skeletonize,
            [self.image_map],
        )
        skeleton = encode_base64(fixtures_path('map_sk_combined_d6.png'))
        assert skeleton == result.output.strip()

    def test_skeletonize_default(self):
        result = self.runner.invoke(
            cli.skeletonize,
            ['-m', 'combined', '-b', 'li', '-d', 6,
             self.image_map],
        )
        skeleton = encode_base64(fixtures_path('map_sk_combined_d6.png'))
        assert skeleton == result.output.strip()

    def test_skeletonize_no_dilation_thin(self):
        result = self.runner.invoke(
            cli.skeletonize,
            ['-m', 'thin', '-d', 0,
             self.image_map],
        )
        skeleton = encode_base64(fixtures_path('map_sk_thin_d0.png'))
        assert skeleton == result.output.strip()

    def test_skeletonize_invert(self):
        result = self.runner.invoke(
            cli.skeletonize,
            ['-m', 'regular', '-d', 0, '-i',
             self.image_map],
        )
        skeleton = encode_base64(fixtures_path('map_sk_regular_d0_invert.png'))
        assert skeleton == result.output.strip()

    def test_command_palette(self):
        palette = [[250, 67, 69], [123, 9, 108]]
        result = self.runner.invoke(
            cli.palette,
            ['{"#fa4345": 3829, "[123, 9, 108]": 982}']
        ).output.strip()
        assert json.loads(result) == palette

    def test_command_palette_file(self):
        palette = [[250, 67, 69], [123, 9, 108]]
        result = self.runner.invoke(
            cli.palette,
            [fixtures_path('palette.json')]
        ).output.strip()
        assert json.loads(result) == palette

    def test_command_graph(self):
        matches = [
            ((0, 0), (3, 3)),
            ((1, 11), (4, 14)),
            ((8, 12), (11, 15)),
        ]
        regions = utils.serialize_json(matches)
        result = self.runner.invoke(
            cli.graph,
            [regions, self.image_grid]
        )
        out = nx.parse_graphml(result.output.strip())
        graph = nx.read_gml(fixtures_path('graph.gml'))
        assert nodeset(out) == nodeset(graph)
        assert edgeset(out) == edgeset(graph)

    def test_command_graph_astar(self):
        matches = [
            ((0, 0), (3, 3)),
            ((1, 11), (4, 14)),
            ((8, 12), (11, 15)),
        ]
        regions = utils.serialize_json(matches)
        result = self.runner.invoke(
            cli.graph,
            [regions, '-pm', 'astar', self.image_grid]
        )

        out = nx.parse_graphml(result.output.strip())
        graph = nx.read_graphml(fixtures_path('graph_astar.graphml'))
        assert nodeset(out) == nodeset(graph)
        assert edgeset(out) == edgeset(graph)

    def test_command_graph_gexf(self):
        matches = [
            ((0, 0), (3, 3)),
            ((1, 11), (4, 14)),
            ((8, 12), (11, 15)),
        ]
        regions = utils.serialize_json(matches)
        result = self.runner.invoke(
            cli.graph,
            [regions, '-f', 'gexf', self.image_grid]
        )
        out = nx.read_gexf(io.StringIO(result.output.strip()))
        graph = nx.read_gexf(fixtures_path('graph.gexf'))
        assert nodeset(out) == nodeset(graph)
        assert edgeset(out) == edgeset(graph)

    def test_command_graph_gexf_tolerance(self):
        matches = [
            ((0, 0), (3, 3)),
            ((1, 11), (4, 14)),
            ((8, 12), (11, 15)),
        ]
        regions = utils.serialize_json(matches)
        result = self.runner.invoke(
            cli.graph,
            [regions, '-f', 'gexf', '-st', 0, self.image_grid]
        )
        out = nx.read_gexf(io.StringIO(result.output.strip()))
        graph = nx.read_gexf(fixtures_path('graph.gexf'))
        assert nodeset(out) == nodeset(graph)
        assert edgeset(out) == edgeset(graph)

    def test_histogram(self):
        result = self.runner.invoke(
            cli.histogram,
            ['-m', 'rgb',
             self.image_map],
        )
        with open(fixtures_path('map_histogram.json'), 'r') as file:
            json_data = json.load(file)
            assert json_data == json.loads(result.output.strip())

    def test_histogram_default(self):
        result = self.runner.invoke(cli.histogram, [self.image_map])
        with open(fixtures_path('map_histogram.json'), 'r') as file:
            json_data = json.load(file)
            assert json_data == json.loads(result.output.strip())

    def test_histogram_hex(self):
        result = self.runner.invoke(
            cli.histogram,
            ['-m', 'hex',
             self.image_map],
        )
        with open(fixtures_path('map_histogram_hex.json'), 'r') as file:
            json_data = json.load(file)
            assert json_data == json.loads(result.output.strip())
