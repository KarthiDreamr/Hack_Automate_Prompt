from unittest.mock import patch, mock_open

from src.cbrne.config_loader import load_config, get_challenge_config


def test_load_config_successfully():
    """Tests that the config is loaded correctly from a mock file."""
    mock_yaml_content = """
base_url: "http://example.com"
automation_settings:
  max_retries: 5
"""
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            config = load_config("dummy_path.yaml")
            assert config is not None
            assert config["base_url"] == "http://example.com"
            assert config["automation_settings"]["max_retries"] == 5


def test_get_challenge_config():
    """Tests that the correct challenge-specific config is retrieved."""
    main_config = {
        "base_url": "http://example.com",
        "challenge_specific_configs": {
            "my_challenge": {"prompt_textarea": "textarea#prompt"}
        },
    }
    challenge_config = get_challenge_config(main_config, "my_challenge")
    assert challenge_config is not None
    assert challenge_config["prompt_textarea"] == "textarea#prompt"
    assert challenge_config["base_url"] == "http://example.com"
