"""
AWS Bedrock adapter.
"""

from typing import List, Dict, Any
import json
from .base import BaseLLMAdapter


class BedrockAdapter(BaseLLMAdapter):
    """Adapter for AWS Bedrock."""

    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)

        try:
            import boto3
            # api_key here is actually the AWS access key
            # AWS secret key should be in kwargs
            aws_secret = kwargs.get("aws_secret_access_key", "")
            region = kwargs.get("region_name", "us-east-1")

            if not api_key or not aws_secret:
                raise ValueError("AWS access key and secret key are required")

            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region,
                aws_access_key_id=api_key,
                aws_secret_access_key=aws_secret
            )
        except ImportError:
            raise ImportError("boto3 package not installed. Run: pip install boto3")

    def get_provider_name(self) -> str:
        return "Bedrock"

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to AWS Bedrock."""
        self.validate_settings(temperature, max_tokens)

        try:
            # Format depends on the model
            if "anthropic" in model.lower():
                # Anthropic Claude format
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                })
            elif "meta" in model.lower() or "llama" in model.lower():
                # Meta Llama format
                prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
                body = json.dumps({
                    "prompt": prompt,
                    "max_gen_len": max_tokens,
                    "temperature": temperature
                })
            else:
                # Default format
                body = json.dumps({
                    "inputText": messages[-1]["content"],
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature
                    }
                })

            response = self.client.invoke_model(
                modelId=model,
                body=body
            )

            response_body = json.loads(response.get('body').read())

            # Parse response based on model
            if "anthropic" in model.lower():
                content = response_body.get("content", [{}])[0].get("text", "")
            elif "meta" in model.lower() or "llama" in model.lower():
                content = response_body.get("generation", "")
            else:
                content = response_body.get("results", [{}])[0].get("outputText", "")

            return {
                "content": content,
                "model": model,
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

        except Exception as e:
            error_msg = str(e)
            if "AccessDeniedException" in error_msg:
                raise Exception(f"Invalid {self.get_provider_name()} credentials or permissions")
            elif "ThrottlingException" in error_msg:
                raise Exception(f"Rate limit exceeded for {self.get_provider_name()}")
            else:
                raise Exception(f"{self.get_provider_name()} API error: {error_msg}")

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get AWS Bedrock models."""
        return [
            {"id": "anthropic.claude-3-5-sonnet-20241022-v2:0", "name": "Claude 3.5 Sonnet", "provider": "Bedrock"},
            {"id": "anthropic.claude-3-opus-20240229-v1:0", "name": "Claude 3 Opus", "provider": "Bedrock"},
            {"id": "meta.llama3-1-405b-instruct-v1:0", "name": "Llama 3.1 405B", "provider": "Bedrock"},
            {"id": "meta.llama3-1-70b-instruct-v1:0", "name": "Llama 3.1 70B", "provider": "Bedrock"},
            {"id": "mistral.mixtral-8x7b-instruct-v0:1", "name": "Mixtral 8x7B", "provider": "Bedrock"},
        ]
