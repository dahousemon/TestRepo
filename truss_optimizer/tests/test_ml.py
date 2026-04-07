"""Tests for the ML prediction pipeline."""

import pytest
import numpy as np

from truss_optimizer.core.truss_model import TrussModel, Material, SupportType
from truss_optimizer.ml.dataset import TrussDatasetGenerator

try:
    from truss_optimizer.ml.model import TrussPredictionModel
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


def make_test_truss() -> TrussModel:
    model = TrussModel("ML Test")
    steel = Material.steel()
    model.add_node(0, 0.0, 0.0, SupportType.PIN)
    model.add_node(1, 4.0, 0.0, SupportType.ROLLER_X)
    model.add_node(2, 2.0, 3.0)
    model.add_element(0, 0, 2, 0.005, steel)
    model.add_element(1, 2, 1, 0.005, steel)
    model.add_element(2, 0, 1, 0.005, steel)
    model.add_load(2, 0, -50e3)
    return model


class TestDatasetGenerator:
    def test_generate_warren(self):
        gen = TrussDatasetGenerator(seed=1)
        model = gen.generate_warren_truss(4, 10.0, 3.0, Material.steel(), 50e3)
        assert model.num_nodes > 0
        assert model.num_elements > 0
        errors = model.validate()
        assert len(errors) == 0

    def test_generate_pratt(self):
        gen = TrussDatasetGenerator(seed=1)
        model = gen.generate_pratt_truss(4, 10.0, 3.0, Material.steel(), 50e3)
        errors = model.validate()
        assert len(errors) == 0

    def test_generate_howe(self):
        gen = TrussDatasetGenerator(seed=1)
        model = gen.generate_howe_truss(4, 10.0, 3.0, Material.steel(), 50e3)
        errors = model.validate()
        assert len(errors) == 0

    def test_generate_simple(self):
        gen = TrussDatasetGenerator(seed=1)
        model = gen.generate_simple_truss(6.0, 2.0, Material.steel(), 30e3)
        assert model.num_nodes == 3
        assert model.num_elements == 3

    def test_generate_random(self):
        gen = TrussDatasetGenerator(seed=42)
        model = gen.generate_random_truss()
        errors = model.validate()
        assert len(errors) == 0


@pytest.mark.skipif(not HAS_SKLEARN, reason="scikit-learn not installed")
class TestMLModel:
    def test_feature_extraction(self):
        model = make_test_truss()
        features = TrussPredictionModel.extract_features(model)
        assert "span" in features
        assert "height" in features
        assert "n_nodes" in features
        assert features["n_nodes"] == 3

    def test_train_and_predict(self):
        np.random.seed(42)
        n_features = 10
        n_elements = 3
        X = np.random.rand(50, n_features)
        y = np.random.rand(50, n_elements) * 0.01

        model = TrussPredictionModel(hidden_layers=(32, 16), max_iter=200)
        result = model.train(X, y)
        assert result.train_r2 > -1  # sanity check
        assert model.is_trained

        preds = model.predict(X[:5])
        assert preds.shape == (5, n_elements)

    def test_save_load_roundtrip(self, tmp_path):
        np.random.seed(42)
        X = np.random.rand(30, 5)
        y = np.random.rand(30, 3)

        model = TrussPredictionModel(hidden_layers=(16,), max_iter=100)
        model.train(X, y)

        path = tmp_path / "test_model.pkl"
        model.save(path)

        loaded = TrussPredictionModel.load(path)
        assert loaded.is_trained

        pred_original = model.predict(X[:3])
        pred_loaded = loaded.predict(X[:3])
        np.testing.assert_array_almost_equal(pred_original, pred_loaded)
