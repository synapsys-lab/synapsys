"""Tests for LTIModel base class helpers."""
import numpy as np
import pytest

from synapsys.core.lti import LTIModel


class TestLTIHelpers:
    def test_as_2d_shape_mismatch_raises(self):
        """_as_2d with wrong shape raises ValueError — covers lti.py:48."""
        with pytest.raises(ValueError, match="Expected shape"):
            LTIModel._as_2d([[1, 2], [3, 4]], shape=(3, 2))
