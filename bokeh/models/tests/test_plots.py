#-----------------------------------------------------------------------------
# Copyright (c) 2012 - 2015, Anaconda, Inc. All rights reserved.
#
# Powered by the Bokeh Development Team.
#
# The full license is in the file LICENSE.txt, distributed with this software.
#-----------------------------------------------------------------------------

from __future__ import absolute_import

from mock import patch
import pytest

from bokeh.plotting import figure
from bokeh.models import GlyphRenderer, Label, Plot, LinearAxis
from bokeh.models.ranges import FactorRange, DataRange1d, Range1d
from bokeh.models.scales import CategoricalScale, LinearScale, LogScale
from bokeh.models.tools import PanTool, Toolbar


class TestPlotSelect(object):

    def setup_method(self):
        self._plot = figure(tools='pan')
        self._plot.circle([1,2,3], [3,2,1], name='foo')

    @patch('bokeh.models.plots.find')
    def test_string_arg(self, mock_find):
        self._plot.select('foo')
        assert mock_find.called
        assert mock_find.call_args[0][1] == dict(name='foo')

    @patch('bokeh.models.plots.find')
    def test_type_arg(self, mock_find):
        self._plot.select(PanTool)
        assert mock_find.called
        assert mock_find.call_args[0][1] == dict(type=PanTool)

    @patch('bokeh.models.plots.find')
    def test_kwargs(self, mock_find):
        kw = dict(name='foo', type=GlyphRenderer)
        self._plot.select(**kw)
        assert mock_find.called
        assert mock_find.call_args[0][1] == kw

    @patch('bokeh.models.plots.find')
    def test_single_selector_kwarg(self, mock_find):
        kw = dict(name='foo', type=GlyphRenderer)
        self._plot.select(selector=kw)
        assert mock_find.called
        assert mock_find.call_args[0][1] == kw

    def test_selector_kwarg_and_extra_kwargs(self):
        with pytest.raises(TypeError) as exc:
            self._plot.select(selector=dict(foo='foo'), bar='bar')
        assert "when passing 'selector' keyword arg, not other keyword args may be present" == str(exc.value)

    def test_bad_arg_type(self):
        with pytest.raises(TypeError) as exc:
            self._plot.select(10)
        assert "selector must be a dictionary, string or plot object." == str(exc.value)

    def test_too_many_args(self):
        with pytest.raises(TypeError) as exc:
            self._plot.select('foo', 'bar')
        assert 'select accepts at most ONE positional argument.' == str(exc.value)

    def test_no_input(self):
        with pytest.raises(TypeError) as exc:
            self._plot.select()
        assert 'select requires EITHER a positional argument, OR keyword arguments.' == str(exc.value)

    def test_arg_and_kwarg(self):
        with pytest.raises(TypeError) as exc:
            self._plot.select('foo', type=PanTool)
        assert 'select accepts EITHER a positional argument, OR keyword arguments (not both).' == str(exc.value)


def test_plot_add_layout_raises_error_if_not_render():
    plot = figure()
    with pytest.raises(ValueError):
        plot.add_layout(Range1d())


def test_plot_add_layout_raises_error_if_plot_already_on_annotation():
    plot = figure()
    with pytest.raises(ValueError):
        plot.add_layout(Label(plot=plot))


def test_plot_add_layout_adds_label_to_plot_renderers():
    plot = figure()
    label = Label()
    plot.add_layout(label)
    assert label in plot.renderers


def test_plot_add_layout_adds_axis_to_renderers_and_side_renderers():
    plot = figure()
    axis = LinearAxis()
    plot.add_layout(axis, 'left')
    assert axis in plot.renderers
    assert axis in plot.left


def test_sizing_mode_property_is_fixed_by_default():
    plot = figure()
    assert plot.sizing_mode is 'fixed'


class BaseTwinAxis(object):
    """Base class for testing extra ranges"""

    def verify_axis(self, axis_name):
        plot = Plot()
        range_obj = getattr(plot, 'extra_{}_ranges'.format(axis_name))
        range_obj['foo_range'] = self.get_range_instance()
        assert range_obj['foo_range']

    def test_x_range(self):
        self.verify_axis('x')

    def test_y_range(self):
        self.verify_axis('y')

    @staticmethod
    def get_range_instance():
        raise NotImplementedError


class TestCategoricalTwinAxis(BaseTwinAxis, object):
    """Test whether extra x and y ranges can be categorical"""

    @staticmethod
    def get_range_instance():
        return FactorRange('foo', 'bar')


class TestLinearTwinAxis(BaseTwinAxis, object):
    """Test whether extra x and y ranges can be Range1d"""

    @staticmethod
    def get_range_instance():
        return Range1d(0, 42)


def test_setting_logo_on_plot_declaration_sets_them_on_toolbar():
    plot = Plot(logo='grey')
    assert plot.toolbar.logo == 'grey', "Remove this test when deprecation cycle is over"


def test_setting_tools_on_plot_declaration_sets_them_on_toolbar():
    pan = PanTool()
    plot = Plot(tools=[pan])
    assert plot.toolbar.tools == [pan], "Remove this test when deprecation cycle is over"


def test_plot_raises_error_if_toolbar_and_logo_are_set():
    with pytest.raises(ValueError):
        Plot(logo='grey', toolbar=Toolbar())


def test_plot_raises_error_if_toolbar_and_tools_are_set():
    with pytest.raises(ValueError):
        Plot(tools=[PanTool()], toolbar=Toolbar())


def test_plot_with_no_title_specified_creates_an_empty_title():
    plot = Plot()
    assert plot.title.text == ""


def test_plot__scale_classmethod():
    assert isinstance(Plot._scale("auto"), LinearScale)
    assert isinstance(Plot._scale("linear"), LinearScale)
    assert isinstance(Plot._scale("log"), LogScale)
    assert isinstance(Plot._scale("categorical"), CategoricalScale)
    with pytest.raises(ValueError):
        Plot._scale("malformed_type")


def test__check_required_scale_has_scales():
    plot = Plot()
    check = plot._check_required_scale()
    assert check == []


def test__check_required_scale_missing_scales():
    plot = Plot(x_scale=None, y_scale=None)
    check = plot._check_required_scale()
    assert check != []


def test__check_compatible_scale_and_ranges_compat_numeric():
    plot = Plot(x_scale=LinearScale(), x_range=Range1d())
    check = plot._check_compatible_scale_and_ranges()
    assert check == []


    plot = Plot(y_scale=LogScale(), y_range=DataRange1d())
    check = plot._check_compatible_scale_and_ranges()
    assert check == []


def test__check_compatible_scale_and_ranges_compat_factor():
    plot = Plot(x_scale=CategoricalScale(), x_range=FactorRange())
    check = plot._check_compatible_scale_and_ranges()
    assert check == []


def test__check_compatible_scale_and_ranges_incompat_numeric_scale_and_factor_range():
    plot = Plot(x_scale=LinearScale(), x_range=FactorRange())
    check = plot._check_compatible_scale_and_ranges()
    assert check != []


def test__check_compatible_scale_and_ranges_incompat_factor_scale_and_numeric_range():
    plot = Plot(x_scale=CategoricalScale(), x_range=DataRange1d())
    check = plot._check_compatible_scale_and_ranges()
    assert check != []
