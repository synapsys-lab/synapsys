"""Tests for synapsys/utils/_fmt.py — box renderer, matrix/pole formatters."""

import numpy as np

from synapsys.utils._fmt import _g, box, fmt_arr, fmt_matrix, fmt_poles


class TestBox:
    def test_title_in_header(self):
        result = box("Foo", ["line1"])
        assert "======= Foo " in result

    def test_min_width_enforced(self):
        result = box("X", [])
        header = result.split("\n")[0]
        assert len(header) >= 40

    def test_content_indented(self):
        result = box("T", ["key : value"])
        assert "  key : value" in result

    def test_footer_matches_header_width(self):
        lines = box("Title", ["a", "b"]).split("\n")
        assert len(lines[0]) == len(lines[-1])

    def test_long_title_expands_width(self):
        long_title = "A" * 50
        result = box(long_title, [])
        header = result.split("\n")[0]
        assert long_title in header
        assert len(header) >= 40


class TestG:
    def test_formats_float(self):
        assert _g(1.0) == "1"
        assert _g(3.14159, 3) == "3.14"


class TestFmtArr:
    def test_basic(self):
        a = np.array([1.0, 2.5, 3.0])
        result = fmt_arr(a)
        assert result.startswith("[")
        assert result.endswith("]")
        assert "2.5" in result


class TestFmtMatrix:
    def test_small_matrix_label_and_borders(self):
        M = np.array([[1.0, 2.0], [3.0, 4.0]])
        lines = fmt_matrix(M, "A")
        assert lines[0].startswith("A = |")
        assert lines[1].startswith("    |")
        assert all(line.endswith("|") for line in lines)
        assert len(lines) == 2

    def test_sign_alignment(self):
        M = np.array([[0.0, 1.0], [-2.0, -5.0]])
        lines = fmt_matrix(M, "A")
        # Positive values get a leading space, negative get '-'
        assert " 0.0000" in lines[0]
        assert "-2.0000" in lines[1]

    def test_large_matrix_fallback(self):
        M = np.zeros((9, 9))
        lines = fmt_matrix(M, "X")
        assert lines == ["X : (9×9) array"]

    def test_large_cols_fallback(self):
        M = np.zeros((2, 9))
        lines = fmt_matrix(M, "B")
        assert "9" in lines[0]


class TestFmtPoles:
    def test_empty_poles(self):
        result = fmt_poles(np.array([]))
        assert result == ["(none)"]

    def test_real_stable_pole(self):
        poles = np.array([-3.0 + 0j])
        lines = fmt_poles(poles)
        assert len(lines) == 1
        assert "-3.0000" in lines[0]
        assert "UNSTABLE" not in lines[0]

    def test_real_unstable_pole(self):
        poles = np.array([2.0 + 0j])
        lines = fmt_poles(poles)
        assert "UNSTABLE" in lines[0]

    def test_complex_conjugate_pair(self):
        poles = np.array([-2.5 + 4.33j, -2.5 - 4.33j])
        lines = fmt_poles(poles)
        # Conjugate pair should produce ONE line (±) and skip the partner
        assert len(lines) == 1
        assert "±" in lines[0]
        assert "ζ" in lines[0]
        assert "ωₙ" in lines[0]

    def test_unpaired_complex_pole(self):
        # Pole with imaginary part but no conjugate partner
        poles = np.array([-1.0 + 2.0j])
        lines = fmt_poles(poles)
        assert len(lines) == 1
        assert "j" in lines[0]
        assert "±" not in lines[0]

    def test_discrete_real_pole(self):
        poles = np.array([0.5 + 0j])
        lines = fmt_poles(poles, is_discrete=True)
        assert "|z|" not in lines[0]  # discrete real shows "(real)"
        assert "real" in lines[0]
        assert "UNSTABLE" not in lines[0]

    def test_discrete_real_unstable_pole(self):
        poles = np.array([1.5 + 0j])
        lines = fmt_poles(poles, is_discrete=True)
        assert "UNSTABLE" in lines[0]

    def test_discrete_complex_pair(self):
        poles = np.array([0.5 + 0.5j, 0.5 - 0.5j])
        lines = fmt_poles(poles, is_discrete=True)
        assert len(lines) == 1
        assert "|z|" in lines[0]
        assert "±" in lines[0]

    def test_discrete_unpaired_complex(self):
        poles = np.array([0.3 + 0.4j])
        lines = fmt_poles(poles, is_discrete=True)
        assert "|z|" in lines[0]
        assert "±" not in lines[0]

    def test_discrete_unstable_complex(self):
        poles = np.array([0.8 + 0.8j, 0.8 - 0.8j])
        lines = fmt_poles(poles, is_discrete=True)
        # |z| = sqrt(0.64+0.64) > 1 → UNSTABLE
        assert "UNSTABLE" in lines[0]
