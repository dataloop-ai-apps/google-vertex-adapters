import os
import base64
import json
import dtlpy as dl
import logging
from anthropic import AnthropicVertex

logger = logging.getLogger("Vertex Claude Adapter")


class ModelAdapter(dl.BaseModelAdapter):
    def __init__(self, model_entity: dl.Model):
        super().__init__(model_entity)
        
    def load(self, local_path, **kwargs):
        # Get model configuration
        self.model_id = self.model_entity.configuration.get('model_id', 'claude-opus-4@20250514')
        self.max_tokens = self.model_entity.configuration.get('max_tokens', 1024)
        
        # Get GCP credentials using the same pattern as other adapters
        raw_credentials = os.environ.get("GCP_SERVICE_ACCOUNT", None)
        try:
            decoded_credentials = base64.b64decode(raw_credentials).decode("utf-8")
            credentials_json = json.loads(decoded_credentials)
            credentials = json.loads(credentials_json['content'])
        except Exception:
            raise ValueError("Unable to decode the service account JSON. "
                             "Please refer to the following guide for proper usage of GCP service accounts with "
                             "Dataloop: https://github.com/dataloop-ai-apps/google-vertex-adapters/blob/main/README.md")
        
        self.project_id = credentials.get('project_id', None)
        self.region = credentials.get('location', 'us-east5')  # Default region for Claude
        
        # Initialize Anthropic Vertex client
        self.client = AnthropicVertex(
            region=self.region,
            project_id=self.project_id,
            credentials=credentials
        )

    def prepare_item_func(self, item: dl.Item):
        """Prepare items for processing - only handles prompt items"""
        # Check if it's a prompt item (JSON with dltype='prompt')
        if ('json' in item.mimetype and 
            item.metadata.get('system', dict()).get('shebang', dict()).get('dltype') == 'prompt'):
            buffer = json.load(item.download(save_locally=False))
            return buffer
        
        # Reject non-prompt items
        else:
            logger.warning(f"Item mimetype {item.mimetype} is not supported. "
                          f"This adapter only works with prompt items (JSON).")
            return None

    def _process_prompt_item(self, prompt_item, prompt_name):
        """Process a prompt item to extract content and generate response"""
        try:
            messages = []
            
            for partial_prompt in prompt_item:
                mimetype = partial_prompt.get('mimetype', '')
                value = partial_prompt.get('value', '')
                
                # Handle text content
                if 'text' in mimetype:
                    messages.append({
                        "type": "text",
                        "text": value
                    })
                
                # Handle image content in prompt
                elif 'image' in mimetype:
                    item_id = value.split("/stream")[0].split("/items/")[-1]
                    image_buffer = dl.items.get(item_id=item_id).download(save_locally=False).getvalue()
                    base64_image = base64.b64encode(image_buffer).decode('utf-8')
                    
                    # Determine image type
                    if 'jpeg' in mimetype or 'jpg' in mimetype:
                        media_type = "image/jpeg"
                    elif 'png' in mimetype:
                        media_type = "image/png"
                    elif 'gif' in mimetype:
                        media_type = "image/gif"
                    elif 'webp' in mimetype:
                        media_type = "image/webp"
                    else:
                        media_type = "image/jpeg"  # Default fallback
                    
                    messages.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image
                        }
                    })
                else:
                    logger.warning(f"Prompt mimetype {mimetype} is not supported. "
                                 f"Please provide text or image content.")
                    continue
            
            if messages:
                return self._call_claude_api_with_messages(messages, prompt_name)
            else:
                logger.warning(f"No valid content found in prompt {prompt_name}")
                return None
                    
        except Exception as e:
            logger.error(f"Error processing prompt item {prompt_name}: {str(e)}")
            return None

    def _call_claude_api_with_messages(self, messages, prompt_name):
        """Make API call to Claude with structured messages"""
        try:
            message = self.client.messages.create(
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": messages
                    }
                ],
                model=self.model_id,
            )
            
            # Extract response text
            if message.content and len(message.content) > 0:
                return message.content[0].text
            else:
                logger.warning(f"Empty response from Claude for prompt {prompt_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Claude API for prompt {prompt_name}: {str(e)}")
            return None

    def predict(self, batch, **kwargs):
        annotations = []
        
        for batch_item in batch:
            ann_collection = dl.AnnotationCollection()
            if isinstance(batch_item, dict) and 'prompts' in batch_item:
                for prompt_name, prompt_content in batch_item.get('prompts').items():
                    response_text = self._process_prompt_item(prompt_content, prompt_name)
                    
                    if response_text:
                        ann_collection.add(
                            annotation_definition=dl.FreeText(text=response_text),
                            prompt_id=prompt_name,
                            model_info={
                                'name': self.model_entity.name,
                                'model_id': self.model_entity.id,
                                'confidence': 1.0
                            }
                        )
                    else:
                        logger.warning(f"No response generated for prompt {prompt_name}")
            
            else:
                logger.error(f"Unsupported batch item type: {type(batch_item)}. "
                           f"This adapter only works with prompt items.")
            
            annotations.append(ann_collection)
            
        return annotations