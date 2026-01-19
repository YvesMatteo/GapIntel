import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import numpy as np

# 1. Mock external dependencies in sys.modules BEFORE importing the code under test
mock_supabase_module = MagicMock()
sys.modules['supabase'] = mock_supabase_module

mock_st_module = MagicMock()
sys.modules['sentence_transformers'] = mock_st_module

# 2. Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 3. Import the module under test - this will now successfully "import" from our mocks
from premium.ml_models.content_clusterer import ContentClusteringEngine

class TestContentClusteringEngine(unittest.TestCase):
    def setUp(self):
        # Setup environment variables
        os.environ['SUPABASE_URL'] = 'https://example.supabase.co'
        os.environ['SUPABASE_SERVICE_KEY'] = 'test-key'
        
        self.patchers = []
        
        # Patch create_client
        self.mock_supabase_client = MagicMock()
        p1 = patch('premium.ml_models.content_clusterer.create_client', return_value=self.mock_supabase_client)
        self.mock_create_client = p1.start()
        self.patchers.append(p1)
        
        # Patch SentenceTransformer
        p2 = patch('premium.ml_models.content_clusterer.SentenceTransformer')
        self.mock_st_class = p2.start()
        self.patchers.append(p2)
        
        self.mock_model = MagicMock()
        self.mock_st_class.return_value = self.mock_model
        self.mock_model.encode.return_value = np.random.rand(1, 384) 

        # Patch PCA and KMeans to avoid sklearn errors with small data
        p3 = patch('premium.ml_models.content_clusterer.PCA')
        self.mock_pca = p3.start()
        self.mock_pca.return_value.fit_transform.side_effect = lambda x: x # Identity transform
        self.patchers.append(p3)
        
        p4 = patch('premium.ml_models.content_clusterer.KMeans')
        self.mock_kmeans = p4.start()
        self.mock_kmeans.return_value.fit_predict.return_value = [0, 1] # Dummy labels
        self.patchers.append(p4)

    def tearDown(self):
        for p in self.patchers:
            p.stop()

    def test_init(self):
        engine = ContentClusteringEngine(use_embeddings=True)
        self.mock_create_client.assert_called()
        self.assertIsNotNone(engine.supabase)
        self.assertTrue(engine.use_embeddings)

    def test_get_cached_embeddings(self):
        engine = ContentClusteringEngine(use_embeddings=True)
        
        mock_response = MagicMock()
        mock_response.data = [
            {'video_id': 'v1', 'embedding': [0.1] * 384},
            {'video_id': 'v2', 'embedding': [0.2] * 384}
        ]
        self.mock_supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response
        
        cache = engine._get_cached_embeddings(['v1', 'v2'])
        self.assertEqual(len(cache), 2)
        self.assertEqual(cache['v1'], [0.1] * 384)

    def test_cache_embeddings(self):
        engine = ContentClusteringEngine(use_embeddings=True)
        embeddings = {'v1': [0.1] * 384}
        
        engine._cache_embeddings(embeddings)
        
        self.mock_supabase_client.table.return_value.upsert.assert_called()
        call_args = self.mock_supabase_client.table.return_value.upsert.call_args[0][0]
        self.assertEqual(len(call_args), 1)
        self.assertEqual(call_args[0]['video_id'], 'v1')

    def test_cluster_flow_generation(self):
        """Test that missing embeddings are generated and cached"""
        engine = ContentClusteringEngine(use_embeddings=True)
        
        # Mock partial cache hit
        mock_response = MagicMock()
        mock_response.data = [{'video_id': 'v1', 'embedding': [0.1] * 384}]
        self.mock_supabase_client.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response
        
        # Mock generation for v2
        expected_embedding_v2 = np.array([[0.9] * 384])
        self.mock_model.encode.return_value = expected_embedding_v2
        
        videos = [
            {'video_id': 'v1', 'title': 'Title 1'},
            {'video_id': 'v2', 'title': 'Title 2'}
        ]
        
        # Make KMeans return match sample size
        self.mock_kmeans.return_value.fit_predict.return_value = [0, 1]
        
        # Run
        embeddings_map = engine._cluster_with_embeddings(videos, n_clusters=2)
        
        # Checks
        self.mock_supabase_client.table.return_value.select.return_value.in_.assert_called()
        self.mock_model.encode.assert_called()
        self.mock_supabase_client.table.return_value.upsert.assert_called()

if __name__ == '__main__':
    unittest.main()
