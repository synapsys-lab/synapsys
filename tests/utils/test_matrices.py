import numpy as np
import pytest

from synapsys.utils.matrices import col, mat, row


class TestMat:
    def test_returns_ndarray(self):
        A = mat([[1, 2], [3, 4]])
        assert isinstance(A, np.ndarray)

    def test_shape(self):
        A = mat([[0, 1], [-2, -3]])
        assert A.shape == (2, 2)

    def test_dtype_is_float(self):
        A = mat([[1, 2], [3, 4]])
        assert A.dtype == np.float64

    def test_values(self):
        A = mat([[1, 2], [3, 4]])
        np.testing.assert_array_equal(A, [[1, 2], [3, 4]])

    def test_single_row(self):
        A = mat([[1, 2, 3]])
        assert A.shape == (1, 3)

    def test_single_column(self):
        A = mat([[1], [2], [3]])
        assert A.shape == (3, 1)

    def test_integer_inputs_converted(self):
        A = mat([[1, 0], [0, 1]])
        assert A.dtype == np.float64

    def test_float_values_preserved(self):
        A = mat([[0.5, -1.5], [2.0, -0.25]])
        np.testing.assert_allclose(A, [[0.5, -1.5], [2.0, -0.25]])


class TestCol:
    def test_returns_column_vector(self):
        v = col(1, 2, 3)
        assert v.shape == (3, 1)

    def test_dtype_is_float(self):
        v = col(0, 1, 2)
        assert v.dtype == np.float64

    def test_values(self):
        v = col(0, 0, 1.5)
        np.testing.assert_allclose(v.flatten(), [0, 0, 1.5])

    def test_single_element(self):
        v = col(7.0)
        assert v.shape == (1, 1)
        assert v[0, 0] == pytest.approx(7.0)

    def test_negative_values(self):
        v = col(-1, -2, -3)
        np.testing.assert_array_equal(v.flatten(), [-1, -2, -3])


class TestRow:
    def test_returns_row_vector(self):
        v = row(1, 0, 0, 0)
        assert v.shape == (1, 4)

    def test_dtype_is_float(self):
        v = row(1, 2, 3)
        assert v.dtype == np.float64

    def test_values(self):
        v = row(1, 2, 3)
        np.testing.assert_allclose(v.flatten(), [1, 2, 3])

    def test_single_element(self):
        v = row(5.0)
        assert v.shape == (1, 1)
        assert v[0, 0] == pytest.approx(5.0)
