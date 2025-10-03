"""Tests for merger web module."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from streamline_vpn.merger.web import (
    app,
    load_cfg,
    run_aggregator,
    run_merger,
    main
)


class TestWebModule:
    """Test cases for web module."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @patch('streamline_vpn.merger.web.load_config')
    def test_load_cfg(self, mock_load_config):
        """Test load_cfg function."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        result = load_cfg()
        
        assert result == mock_config
        mock_load_config.assert_called_once()

    @patch('streamline_vpn.merger.web.run_pipeline')
    @patch('streamline_vpn.merger.web.load_cfg')
    def test_run_aggregator(self, mock_load_cfg, mock_run_pipeline):
        """Test run_aggregator function."""
        mock_cfg = MagicMock()
        mock_load_cfg.return_value = mock_cfg
        
        mock_output_dir = Path("/test/output")
        mock_files = [Path("/test/file1.txt"), Path("/test/file2.txt")]
        mock_run_pipeline.return_value = (mock_output_dir, mock_files)
        
        # Mock asyncio.run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = (mock_output_dir, mock_files)
            
            result = run_aggregator()
            
            assert result == (mock_output_dir, mock_files)
            mock_load_cfg.assert_called_once()
            mock_asyncio_run.assert_called_once()

    @patch('streamline_vpn.merger.web.detect_and_run')
    @patch('streamline_vpn.merger.web.load_cfg')
    @patch('streamline_vpn.merger.web.CONFIG')
    def test_run_merger(self, mock_config, mock_load_cfg, mock_detect_and_run):
        """Test run_merger function."""
        mock_cfg = MagicMock()
        mock_cfg.output_dir = "/test/output"
        mock_load_cfg.return_value = mock_cfg
        
        run_merger()
        
        mock_load_cfg.assert_called_once()
        assert mock_config.output_dir == "/test/output"
        mock_detect_and_run.assert_called_once()

    @patch('streamline_vpn.merger.web.run_aggregator')
    def test_aggregate_endpoint(self, mock_run_aggregator, client):
        """Test /aggregate endpoint."""
        mock_output_dir = Path("/test/output")
        mock_files = [Path("/test/file1.txt"), Path("/test/file2.txt")]
        mock_run_aggregator.return_value = (mock_output_dir, mock_files)
        
        response = client.get('/aggregate')
        
        assert response.status_code == 200
        data = response.get_json()
        # On Windows, paths might use backslashes, so normalize for comparison
        assert data['output_dir'].replace('\\', '/') == "/test/output"
        expected_files = ["/test/file1.txt", "/test/file2.txt"]
        actual_files = [f.replace('\\', '/') for f in data['files']]
        assert actual_files == expected_files

    @patch('streamline_vpn.merger.web.run_merger')
    def test_merge_endpoint(self, mock_run_merger, client):
        """Test /merge endpoint."""
        mock_run_merger.return_value = None
        
        response = client.get('/merge')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == "merge complete"
        mock_run_merger.assert_called_once()

    @patch('streamline_vpn.merger.web.load_cfg')
    def test_report_endpoint_html_exists(self, mock_load_cfg, client):
        """Test /report endpoint when HTML report exists."""
        mock_cfg = MagicMock()
        mock_cfg.output_dir = "/test/output"
        mock_load_cfg.return_value = mock_cfg
        
        # Mock the Path operations more specifically
        with patch('streamline_vpn.merger.web.Path') as mock_path_class:
            # Create mock path instances
            mock_html_path = MagicMock()
            mock_json_path = MagicMock()
            
            # Set up the path constructor to return appropriate instances
            def path_constructor(path_arg):
                path_str = str(path_arg)
                if "vpn_report.html" in path_str:
                    mock_html_path.exists.return_value = True
                    return mock_html_path
                elif "vpn_report.json" in path_str:
                    mock_json_path.exists.return_value = False
                    return mock_json_path
                return MagicMock()
            
            mock_path_class.side_effect = path_constructor
            
            with patch('streamline_vpn.merger.web.send_file') as mock_send_file:
                mock_send_file.return_value = "HTML report content"
                
                response = client.get('/report')
                
                mock_send_file.assert_called_once()

    @patch('streamline_vpn.merger.web.load_cfg')
    def test_report_endpoint_json_exists(self, mock_load_cfg, client):
        """Test /report endpoint when only JSON report exists."""
        mock_cfg = MagicMock()
        mock_cfg.output_dir = "/test/output"
        mock_load_cfg.return_value = mock_cfg
        
        test_data = {"test": "data", "count": 42}
        
        # Mock the Path class to control both HTML and JSON path behavior
        with patch('streamline_vpn.merger.web.Path') as mock_path_class:
            # Create mock path instances
            mock_html_path = MagicMock()
            mock_json_path = MagicMock()
            
            # Set up the path constructor to return appropriate instances
            def path_constructor(path_arg):
                path_str = str(path_arg)
                if "vpn_report.html" in path_str:
                    mock_html_path.exists.return_value = False
                    return mock_html_path
                elif "vpn_report.json" in path_str:
                    mock_json_path.exists.return_value = True
                    mock_json_path.read_text.return_value = json.dumps(test_data)
                    return mock_json_path
                return MagicMock()
            
            mock_path_class.side_effect = path_constructor
            
            response = client.get('/report')
            
            assert response.status_code == 200
            assert "VPN Report" in response.get_data(as_text=True)
            assert "test" in response.get_data(as_text=True)

    @patch('streamline_vpn.merger.web.load_cfg')
    def test_report_endpoint_no_report(self, mock_load_cfg, client):
        """Test /report endpoint when no report exists."""
        mock_cfg = MagicMock()
        mock_cfg.output_dir = "/test/output"
        mock_load_cfg.return_value = mock_cfg
        
        # Mock the Path class so both HTML and JSON don't exist
        with patch('streamline_vpn.merger.web.Path') as mock_path_class:
            def path_constructor(path_arg):
                mock_path = MagicMock()
                mock_path.exists.return_value = False
                return mock_path
            
            mock_path_class.side_effect = path_constructor
            
            response = client.get('/report')
            
            assert response.status_code == 404
            assert "Report not found" in response.get_data(as_text=True)

    @patch('streamline_vpn.merger.web.app.run')
    def test_main(self, mock_app_run):
        """Test main function."""
        main()
        mock_app_run.assert_called_once()

    def test_main_module_execution(self):
        """Test module execution."""
        # This tests the main function directly
        with patch('streamline_vpn.merger.web.app.run') as mock_app_run:
            main()
            mock_app_run.assert_called_once()


class TestWebModuleIntegration:
    """Integration tests for web module."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_app_configuration(self):
        """Test Flask app configuration."""
        assert app.name == 'streamline_vpn.merger.web'
        assert hasattr(app, 'test_client')

    def test_routes_exist(self):
        """Test that all expected routes exist."""
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/aggregate' in rules
        assert '/merge' in rules
        assert '/report' in rules

    @patch('streamline_vpn.merger.web.run_aggregator')
    def test_aggregate_endpoint_error_handling(self, mock_run_aggregator, client):
        """Test /aggregate endpoint error handling."""
        mock_run_aggregator.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            client.get('/aggregate')

    @patch('streamline_vpn.merger.web.run_merger')
    def test_merge_endpoint_error_handling(self, mock_run_merger, client):
        """Test /merge endpoint error handling."""
        mock_run_merger.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            client.get('/merge')


class TestWebModuleEdgeCases:
    """Edge case tests for web module."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @patch('streamline_vpn.merger.web.load_cfg')
    def test_report_endpoint_invalid_json(self, mock_load_cfg, client):
        """Test /report endpoint with invalid JSON."""
        mock_cfg = MagicMock()
        mock_cfg.output_dir = "/test/output"
        mock_load_cfg.return_value = mock_cfg
        
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('pathlib.Path.read_text') as mock_read_text:
                # HTML doesn't exist, JSON does but is invalid
                mock_exists.side_effect = [False, True]
                mock_read_text.return_value = "invalid json"
                
                with pytest.raises(json.JSONDecodeError):
                    client.get('/report')

    @patch('streamline_vpn.merger.web.load_config')
    def test_load_cfg_with_path(self, mock_load_config):
        """Test load_cfg with specific path."""
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        result = load_cfg()
        
        # Verify it was called with the CONFIG_PATH
        mock_load_config.assert_called_once()
        args = mock_load_config.call_args[0]
        assert str(args[0]).endswith('config.yaml')

    @patch('streamline_vpn.merger.web.run_pipeline')
    @patch('streamline_vpn.merger.web.load_cfg')
    def test_run_aggregator_with_constants(self, mock_load_cfg, mock_run_pipeline):
        """Test run_aggregator uses correct constants."""
        mock_cfg = MagicMock()
        mock_load_cfg.return_value = mock_cfg
        
        mock_output_dir = Path("/test/output")
        mock_files = [Path("/test/file1.txt")]
        
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = (mock_output_dir, mock_files)
            
            run_aggregator()
            
            # Verify asyncio.run was called with the pipeline function
            mock_asyncio_run.assert_called_once()

