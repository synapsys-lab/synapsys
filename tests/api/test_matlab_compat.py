"""Tests for edge-cases in matlab_compat API layer."""
import numpy as np
import pytest

from synapsys.api.matlab_compat import parallel, series, tf


class TestSeriesParallel:
    def test_series_no_args_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            series()

    def test_parallel_no_args_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            parallel()


class TestTfFactory:
    def test_tf_none_num_raises(self):
        with pytest.raises(TypeError):
            tf(None, [1, 1])

    def test_tf_none_den_raises(self):
        with pytest.raises(TypeError):
            tf([1], None)
