"""Tests for provider adapters."""

import pytest

from llmgine.providers.utils import detect_provider, get_required_headers
from llmgine.providers.openai.adapter import OpenAIAdapter
from llmgine.providers.anthropic.adapter import AnthropicAdapter
from llmgine.providers.gemini.adapter import GeminiAdapter
from llmgine.unified.models import ContentBlock, UnifiedMessage, UnifiedRequest

# Create adapter instances for testing
openai_adapter = OpenAIAdapter()
anthropic_adapter = AnthropicAdapter()
gemini_adapter = GeminiAdapter()

# Compatibility functions for tests
def to_openai_format(request):
    return openai_adapter.to_provider_request(request)

def to_anthropic_format(request):
    return anthropic_adapter.to_provider_request(request)

def to_gemini_format(request):
    return gemini_adapter.to_provider_request(request)


class TestProviderDetection:
    """Test provider detection from model names."""
    
    def test_openai_detection(self):
        """Test OpenAI model detection."""
        assert detect_provider("gpt-4o") == "openai"
        assert detect_provider("gpt-4o-mini") == "openai"
        assert detect_provider("gpt-3.5-turbo") == "openai"
        assert detect_provider("o1-preview") == "openai"
        assert detect_provider("o3-mini") == "openai"
    
    def test_anthropic_detection(self):
        """Test Anthropic model detection."""
        assert detect_provider("claude-3-5-sonnet-20241022") == "anthropic"
        assert detect_provider("claude-3-opus-20240229") == "anthropic"
        assert detect_provider("claude-instant-1.2") == "anthropic"
    
    def test_gemini_detection(self):
        """Test Gemini model detection."""
        assert detect_provider("gemini-2.0-flash") == "gemini"
        assert detect_provider("gemini-pro") == "gemini"
        assert detect_provider("gemini-pro-vision") == "gemini"
    
    def test_unknown_model(self):
        """Test error for unknown model."""
        with pytest.raises(ValueError, match="Cannot detect provider"):
            detect_provider("unknown-model")


class TestOpenAIAdapter:
    """Test OpenAI format conversion."""
    
    def test_simple_text_conversion(self):
        """Test converting simple text messages."""
        request = UnifiedRequest(
            model="gpt-4o-mini",
            messages=[
                UnifiedMessage(role="system", content="Be helpful"),
                UnifiedMessage(role="user", content="Hello"),
            ],
            temperature=0.7,
            max_tokens=100,
        )
        
        result = to_openai_format(request)
        
        assert result["model"] == "gpt-4o-mini"
        assert result["temperature"] == 0.7
        assert result["max_tokens"] == 100
        assert result["stream"] is False
        assert len(result["messages"]) == 2
        assert result["messages"][0] == {"role": "system", "content": "Be helpful"}
        assert result["messages"][1] == {"role": "user", "content": "Hello"}
    
    def test_multimodal_conversion(self):
        """Test converting multimodal content."""
        request = UnifiedRequest(
            model="gpt-4o",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(type="text", text="What's in this image?"),
                        ContentBlock(
                            type="image",
                            image_url="https://example.com/image.jpg"
                        ),
                    ]
                )
            ],
        )
        
        result = to_openai_format(request)
        
        content = result["messages"][0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0] == {"type": "text", "text": "What's in this image?"}
        assert content[1] == {
            "type": "image_url",
            "image_url": {"url": "https://example.com/image.jpg"}
        }
    
    def test_base64_image_conversion(self):
        """Test converting base64 images."""
        request = UnifiedRequest(
            model="gpt-4o",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(
                            type="image",
                            image_base64="iVBORw0KGgoAAAANS...",
                            mime_type="image/png"
                        ),
                    ]
                )
            ],
        )
        
        result = to_openai_format(request)
        
        content = result["messages"][0]["content"]
        assert content[0]["image_url"]["url"] == "data:image/png;base64,iVBORw0KGgoAAAANS..."


class TestAnthropicAdapter:
    """Test Anthropic format conversion."""
    
    def test_system_prompt_extraction(self):
        """Test system prompt is extracted to separate field."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(role="system", content="Be helpful"),
                UnifiedMessage(role="user", content="Hello"),
            ],
            max_tokens=1024,
        )
        
        result = to_anthropic_format(request)
        
        assert result["model"] == "claude-3-5-sonnet-20241022"
        assert result["system"] == "Be helpful"
        assert result["max_tokens"] == 1024
        assert len(result["messages"]) == 1
        assert result["messages"][0] == {"role": "user", "content": "Hello"}
    
    def test_multiple_system_messages(self):
        """Test multiple system messages are combined."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(role="system", content="Be helpful"),
                UnifiedMessage(role="system", content="Be concise"),
                UnifiedMessage(role="user", content="Hello"),
            ],
        )
        
        result = to_anthropic_format(request)
        
        assert result["system"] == "Be helpful\nBe concise"
        assert len(result["messages"]) == 1
    
    def test_system_field_priority(self):
        """Test that system field takes priority over system messages."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(role="user", content="Hello"),
            ],
            system="Direct system prompt",
        )
        
        result = to_anthropic_format(request)
        
        assert result["system"] == "Direct system prompt"
    
    def test_base64_image_support(self):
        """Test base64 image conversion."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(type="text", text="What's this?"),
                        ContentBlock(
                            type="image",
                            image_base64="iVBORw0KGgoAAAANS...",
                            mime_type="image/png"
                        ),
                    ]
                )
            ],
        )
        
        result = to_anthropic_format(request)
        
        content = result["messages"][0]["content"]
        assert len(content) == 2
        assert content[0] == {"type": "text", "text": "What's this?"}
        assert content[1] == {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": "iVBORw0KGgoAAAANS...",
            }
        }
    
    def test_url_image_error(self):
        """Test error when using URL images."""
        request = UnifiedRequest(
            model="claude-3-5-sonnet-20241022",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(
                            type="image",
                            image_url="https://example.com/image.jpg"
                        ),
                    ]
                )
            ],
        )
        
        with pytest.raises(ValueError, match="base64 encoded images"):
            to_anthropic_format(request)


class TestGeminiAdapter:
    """Test Gemini format conversion."""
    
    def test_role_mapping(self):
        """Test assistant role is mapped to model."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[
                UnifiedMessage(role="user", content="Hello"),
                UnifiedMessage(role="assistant", content="Hi there!"),
                UnifiedMessage(role="user", content="How are you?"),
            ],
        )
        
        result = to_gemini_format(request)
        
        assert len(result["contents"]) == 3
        assert result["contents"][0]["role"] == "user"
        assert result["contents"][1]["role"] == "model"
        assert result["contents"][2]["role"] == "user"
    
    def test_generation_config(self):
        """Test generation config settings."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[UnifiedMessage(role="user", content="Hello")],
            temperature=0.9,
            max_tokens=500,
        )
        
        result = to_gemini_format(request)
        
        assert result["generationConfig"]["temperature"] == 0.9
        assert result["generationConfig"]["maxOutputTokens"] == 500
    
    def test_system_instruction(self):
        """Test system instruction handling."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[
                UnifiedMessage(role="system", content="Be creative"),
                UnifiedMessage(role="user", content="Tell me a story"),
            ],
        )
        
        result = to_gemini_format(request)
        
        assert "systemInstruction" in result
        assert result["systemInstruction"]["parts"] == [{"text": "Be creative"}]
        assert len(result["contents"]) == 1
    
    def test_parts_structure(self):
        """Test parts structure for content."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(type="text", text="Analyze this:"),
                        ContentBlock(
                            type="image",
                            image_base64="iVBORw0KGgoAAAANS...",
                            mime_type="image/jpeg"
                        ),
                    ]
                )
            ],
        )
        
        result = to_gemini_format(request)
        
        parts = result["contents"][0]["parts"]
        assert len(parts) == 2
        assert parts[0] == {"text": "Analyze this:"}
        assert parts[1] == {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": "iVBORw0KGgoAAAANS...",
            }
        }
    
    def test_gcs_url_support(self):
        """Test Google Cloud Storage URL support."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(
                            type="image",
                            image_url="gs://bucket/image.jpg"
                        ),
                    ]
                )
            ],
        )
        
        result = to_gemini_format(request)
        
        parts = result["contents"][0]["parts"]
        assert parts[0] == {"file_data": {"file_uri": "gs://bucket/image.jpg"}}
    
    def test_non_gcs_url_error(self):
        """Test error for non-GCS URLs."""
        request = UnifiedRequest(
            model="gemini-2.0-flash",
            messages=[
                UnifiedMessage(
                    role="user",
                    content=[
                        ContentBlock(
                            type="image",
                            image_url="https://example.com/image.jpg"
                        ),
                    ]
                )
            ],
        )
        
        with pytest.raises(ValueError, match="Google Cloud Storage URLs"):
            to_gemini_format(request)


class TestHeaders:
    """Test required headers for providers."""
    
    def test_openai_headers(self):
        """Test OpenAI headers."""
        headers = get_required_headers("openai")
        assert headers["Content-Type"] == "application/json"
    
    def test_anthropic_headers(self):
        """Test Anthropic headers."""
        headers = get_required_headers("anthropic")
        assert headers["Content-Type"] == "application/json"
        assert headers["anthropic-version"] == "2023-06-01"
    
    def test_gemini_headers(self):
        """Test Gemini headers."""
        headers = get_required_headers("gemini")
        assert headers["Content-Type"] == "application/json"
