"""
Google adapter for Gemini models.
"""

from typing import List, Dict, Any
from .base import BaseLLMAdapter

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleAdapter(BaseLLMAdapter):
    """Adapter for Google Gemini models."""
    
    def __init__(self, api_key: str, **kwargs):
        super().__init__(api_key, **kwargs)
        if not GOOGLE_AVAILABLE:
            raise ImportError("google-generativeai package not installed. Install with: pip install google-generativeai")
        if not api_key:
            raise ValueError("Google API key is required")
        genai.configure(api_key=api_key)
        self.client = genai
    
    def get_provider_name(self) -> str:
        return "Google"
    
    def _convert_tools_to_gemini_format(self, tools: List[Dict[str, Any]]) -> List[Any]:
        """
        Convert OpenAI-style function tools to Gemini format.
        
        Gemini expects tools as FunctionDeclaration objects from genai.protos.
        """
        try:
            # Access protos from the genai module
            protos = genai.protos
            
            type_map = {
                "string": protos.Type.STRING,
                "integer": protos.Type.INTEGER,
                "number": protos.Type.NUMBER,
                "boolean": protos.Type.BOOLEAN,
                "array": protos.Type.ARRAY,
                "object": protos.Type.OBJECT
            }

            def build_schema(param: Dict[str, Any]) -> protos.Schema:
                param_type = param.get("type")
                if not param_type:
                    param_type = "object" if "properties" in param else "string"

                schema = protos.Schema(
                    type_=type_map.get(param_type, protos.Type.STRING),
                    description=param.get("description", "")
                )

                if param_type == "object" and "properties" in param:
                    nested_props = {
                        name: build_schema(nested_param)
                        for name, nested_param in param["properties"].items()
                    }
                    schema.properties = nested_props
                    if "required" in param:
                        schema.required = list(param.get("required", []))

                if param_type == "array":
                    items_param = param.get("items") or {"type": "string"}
                    schema.items = build_schema(items_param)

                return schema

            gemini_tools = []
            
            for tool in tools:
                if tool.get("type") == "function" and "function" in tool:
                    func = tool["function"]
                    params = func.get("parameters", {})
                    
                    properties = {}
                    if "properties" in params:
                        for name, param in params["properties"].items():
                            properties[name] = build_schema(param)
                    
                    # Create FunctionDeclaration
                    function_decl = protos.FunctionDeclaration(
                        name=func.get("name", ""),
                        description=func.get("description", ""),
                        parameters=protos.Schema(
                            type_=protos.Type.OBJECT,
                            properties=properties,
                            required=params.get("required", [])
                        )
                    )
                    gemini_tools.append(function_decl)
            
            return gemini_tools if gemini_tools else None
        except (ImportError, AttributeError) as e:
            # Fallback: if protos not available, return None (tools won't work)
            # This allows the request to proceed without function calling
            return None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs
    ) -> Dict[str, Any]:
        """Send chat request to Google Gemini."""
        self.validate_settings(temperature, max_tokens)
        
        try:
            # Extract tools from kwargs (tools should not be in GenerationConfig)
            tools = kwargs.pop("tools", None)
            tool_choice = kwargs.pop("tool_choice", None)
            
            # Configure generation config (without tools)
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                **kwargs  # Remaining kwargs (excluding tools)
            }
            
            # Get model - pass tools to model constructor if provided
            model_kwargs = {"model_name": model, "generation_config": generation_config}
            if tools:
                try:
                    # Convert OpenAI-style tools to Gemini format
                    gemini_tools = self._convert_tools_to_gemini_format(tools)
                    if gemini_tools:
                        model_kwargs["tools"] = gemini_tools
                except Exception as e:
                    # If tool conversion fails, continue without tools
                    # This prevents the entire request from failing
                    print(f"⚠️  Warning: Could not convert tools for Gemini: {e}")
            
            # Format messages for Gemini
            # Gemini uses a different format - convert messages to chat history
            chat_history = []
            system_instruction = None
            
            for msg in messages:
                role = msg["role"]
                content = msg["content"]
                
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    chat_history.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    chat_history.append({"role": "model", "parts": [content]})

            # Pass system instruction if found
            if system_instruction:
                model_kwargs["system_instruction"] = system_instruction
            
            gemini_model = self.client.GenerativeModel(**model_kwargs)

            
            # Start chat
            chat = gemini_model.start_chat(history=chat_history[:-1] if len(chat_history) > 1 else [])
            
            # Send message
            last_message = chat_history[-1]["parts"][0] if chat_history else ""
            response = chat.send_message(last_message)
            
            # Extract text
            content = response.text if hasattr(response, 'text') else str(response)
            
            # Get usage info if available (usage_metadata is a protobuf message, not a dict)
            usage_metadata = getattr(response, 'usage_metadata', None)
            usage = {
                "prompt_tokens": getattr(usage_metadata, 'prompt_token_count', 0) if usage_metadata else 0,
                "completion_tokens": getattr(usage_metadata, 'candidates_token_count', 0) if usage_metadata else 0,
                "total_tokens": 0
            }
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
            
            return {
                "content": content,
                "model": model,
                "usage": usage
            }
            
        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get available Google Gemini models.
        """
        try:
            models = self.client.list_models()
            
            gemini_models = []
            for model in models:
                model_name = model.name
                # Only include Gemini models
                if 'gemini' in model_name.lower():
                    gemini_models.append({
                        "id": model_name.split('/')[-1],  # Extract model ID
                        "name": model_name.split('/')[-1].replace('-', ' ').title(),
                        "provider": "Google",
                        "description": f"Google {model_name.split('/')[-1]} model",
                        "context_window": getattr(model, 'input_token_limit', 0)
                    })
            
            return gemini_models
            
        except Exception as e:
            # Fallback to known models
            return [
                {
                    "id": "gemini-1.5-pro",
                    "name": "Gemini 1.5 Pro",
                    "provider": "Google",
                    "description": "Most capable Gemini model",
                    "context_window": 2000000
                },
                {
                    "id": "gemini-1.5-flash",
                    "name": "Gemini 1.5 Flash",
                    "provider": "Google",
                    "description": "Fast and efficient Gemini model",
                    "context_window": 1000000
                },
                {
                    "id": "gemini-pro",
                    "name": "Gemini Pro",
                    "provider": "Google",
                    "description": "Standard Gemini model",
                    "context_window": 30720
                }
            ]
