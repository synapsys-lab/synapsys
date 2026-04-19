import numpy as np
import pytest

from synapsys.broker.topic import Topic, TopicRegistry


class TestTopic:
    def test_validate_correct_shape_returns_contiguous_array(self):
        topic = Topic("plant/y", shape=(3,))
        data = np.array([1.0, 2.0, 3.0])
        result = topic.validate(data)
        assert result.shape == (3,)
        assert result.flags["C_CONTIGUOUS"]

    def test_validate_wrong_shape_raises(self):
        topic = Topic("plant/y", shape=(3,))
        with pytest.raises(ValueError):
            topic.validate(np.array([1.0, 2.0]))

    def test_validate_coerces_dtype(self):
        topic = Topic("plant/y", shape=(2,))
        result = topic.validate(np.array([1, 2], dtype=np.int32))
        assert result.dtype == np.float64

    def test_size_1d(self):
        assert Topic("t", shape=(4,)).size == 4

    def test_size_2d(self):
        assert Topic("t", shape=(2, 3)).size == 6

    def test_topic_is_hashable(self):
        t = Topic("plant/y", shape=(1,))
        assert hash(t) is not None
        d = {t: "value"}
        assert d[t] == "value"

    def test_equal_topics_are_equal(self):
        assert Topic("a", shape=(2,)) == Topic("a", shape=(2,))

    def test_different_shape_topics_not_equal(self):
        assert Topic("a", shape=(2,)) != Topic("a", shape=(3,))


class TestTopicRegistry:
    def test_register_and_get(self):
        reg = TopicRegistry()
        t = Topic("plant/y", shape=(1,))
        reg.register(t)
        assert reg.get("plant/y") is t

    def test_get_unknown_raises(self):
        reg = TopicRegistry()
        with pytest.raises(KeyError):
            reg.get("nonexistent")

    def test_register_same_topic_twice_is_idempotent(self):
        reg = TopicRegistry()
        t = Topic("plant/y", shape=(1,))
        reg.register(t)
        reg.register(t)  # should not raise

    def test_register_duplicate_name_different_schema_raises(self):
        reg = TopicRegistry()
        reg.register(Topic("plant/y", shape=(1,)))
        with pytest.raises(ValueError, match="already registered"):
            reg.register(Topic("plant/y", shape=(2,)))

    def test_all_returns_copy(self):
        reg = TopicRegistry()
        reg.register(Topic("a", shape=(1,)))
        reg.register(Topic("b", shape=(2,)))
        assert set(reg.all.keys()) == {"a", "b"}
