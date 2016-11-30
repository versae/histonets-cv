#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_histonets
----------------------------------

Tests for `histonets` module.
"""
import io
import os
import tempfile
import unittest

import cv2
import numpy as np
from click.testing import CliRunner

import histonets
from histonets import cli


class TestHistonets(unittest.TestCase):
    def setUp(self):
        self.image = cv2.imread(os.path.join('tests', 'test.png'))

    def test_adjust_high_contrast(self):
        image = self.image
        image_high_contrast = histonets.adjust_contrast(image, 50)
        test_high_contrast = cv2.imread('tests/test_high_contrast.png')
        assert np.array_equal(image_high_contrast, test_high_contrast)

    def test_adjust_low_contrast(self):
        image = self.image
        image_low_contrast = histonets.adjust_contrast(image, -50)
        test_low_contrast = cv2.imread('tests/test_low_contrast.png')
        assert np.array_equal(image_low_contrast, test_low_contrast)

    def test_contrast_value_parsing(self):
        image = self.image
        assert np.array_equal(
            histonets.adjust_contrast(image, -150),
            histonets.adjust_contrast(image, -100)
        )
        assert np.array_equal(
            histonets.adjust_contrast(image, 150),
            histonets.adjust_contrast(image, 100)
        )

    def test_lower_brightness(self):
        image = self.image
        image_low_brightness = histonets.adjust_brightness(image, -50)
        test_low_brightness = cv2.imread('tests/test_brightness_darken.png')
        assert np.array_equal(image_low_brightness, test_low_brightness)

    def test_higher_brightness(self):
        image = self.image
        image_high_brightness = histonets.adjust_brightness(image, 50)
        test_high_brightness = cv2.imread('tests/test_brightness_lighten.png')
        assert np.array_equal(image_high_brightness, test_high_brightness)

    def test_brightness_value_parsing(self):
        image = self.image
        assert np.array_equal(
            histonets.adjust_brightness(image, -150),
            histonets.adjust_brightness(image, -100)
        )
        assert np.array_equal(
            histonets.adjust_brightness(image, 150),
            histonets.adjust_brightness(image, 100)
        )

    def test_smooth_image(self):
        image = self.image
        smooth_image = histonets.smooth_image(image, 50)
        test_smooth_image = cv2.imread('tests/smooth50.png')
        assert np.array_equal(smooth_image, test_smooth_image)

    def test_smooth_image_value_parsing(self):
        image = self.image
        test_smooth100_image = cv2.imread('tests/smooth100.png')
        test_smooth0_image = cv2.imread('tests/smooth0.png')
        assert np.array_equal(
            histonets.smooth_image(image, 150),
            test_smooth100_image
            )
        assert np.array_equal(
            histonets.smooth_image(image, -50),
            test_smooth0_image
            )


class TestHistonetsCli(unittest.TestCase):
    def setUp(self):
        self.image_url = 'http://httpbin.org/image/jpeg'
        self.image_file = 'file://' + os.path.join('tests', 'test.png')
        self.image_404 = 'file:///not_found.png'
        self.image_jpg = os.path.join('tests', 'test.jpg')
        self.image_png = os.path.join('tests', 'test.png')
        self.image_b64 = os.path.join('tests', 'test.b64')
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

    def test_io_handler_to_file_as_png(self):
        result = self.runner.invoke(cli.download,
            [self.image_file, '--output', self.tmp_png]
        )
        assert 'Error' not in result.output
        assert len(result.output) == 0
        image_png = cv2.imread(self.image_png)
        tmp_png = cv2.imread(self.tmp_png)
        assert np.array_equal(image_png, tmp_png)

    def test_io_handler_to_file_as_jpg(self):
        result = self.runner.invoke(cli.download,
            [self.image_file, '--output', self.tmp_jpg]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_jpg = cv2.imread(self.image_jpg)
        tmp_jpg = cv2.imread(self.tmp_jpg)
        assert np.array_equal(image_jpg, tmp_jpg)

    def test_io_handler_to_file_as_png(self):
        result = self.runner.invoke(cli.download,
            [self.image_file, '--output', self.tmp_png]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_png = cv2.imread(self.image_png)
        tmp_png = cv2.imread(self.tmp_png)
        assert np.array_equal(image_png, tmp_png)

    def test_io_handler_to_file_and_convert_to_tiff(self):
        result = self.runner.invoke(cli.download,
            [self.image_file, '--output', self.tmp_tiff]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_png = cv2.imread(self.image_png)
        tmp_tiff = cv2.imread(self.tmp_tiff)
        assert np.array_equal(image_png, tmp_tiff)

    def test_io_handler_to_file_with_no_format(self):
        result = self.runner.invoke(cli.download,
            [self.image_file, '--output', self.tmp_no_format]
        )
        assert 'Error' not in result.output
        assert len(result.output.strip()) == 0
        image_png = cv2.imread(self.image_png)
        tmp_no_format = cv2.imread(self.tmp_no_format)
        assert np.array_equal(image_png, tmp_no_format)

    def test_io_handler_to_file_with_invalid_format(self):
        result = self.runner.invoke(cli.download,
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
