import os
import base64
import json
import dtlpy as dl
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, Image, FinishReason
from google.oauth2 import service_account

logger = logging.getLogger("Vertex Gemini Adapter")


class ModelAdapter(dl.BaseModelAdapter):
    def __init__(self, model_entity: dl.Model):
        super().__init__(model_entity)

        self.max_token = self.model_entity.configuration.get('max_token', 1024)
        self.temperature = self.model_entity.configuration.get('temperature', 0.2)
        self.top_p = self.model_entity.configuration.get('top_p', 0.7)
        self.top_k = self.model_entity.configuration.get('top_k', 40)
        self.context = self.model_entity.configuration.get('system_prompt', '')
        self.model_name = self.model_entity.configuration.get('model_name', "gemini-2.5-flash")

        raw_credentials = os.environ.get("GCP_SERVICE_ACCOUNT", None)
        try:
            decoded_credentials = base64.b64decode(raw_credentials).decode("utf-8")
            credentials_json = json.loads(decoded_credentials)
            credentials = json.loads(credentials_json['content'])
        except Exception:
            raise ValueError("Unable to decode the service account JSON. "
                             "Please refer to the following guide for proper usage of GCP service accounts with "
                             "Dataloop: https://github.com/dataloop-ai-apps/google-vertex-adapters/blob/main/README.md")
        project_id = credentials.get('project_id', None)
        credentials = service_account.Credentials.from_service_account_info(credentials)
        vertexai.init(credentials=credentials, project=project_id)

    def load(self, local_path, **kwargs):
        pass

    def prepare_item_func(self, item: dl.Item):
        if 'json' not in item.mimetype or item.metadata.get('system', dict()).get('shebang', dict()).get(
                'dltype') != 'prompt':
            logger.warning(f"Item is not a JSON file or a Prompt item.")
            return None
        buffer = json.load(item.download(save_locally=False))
        return buffer

    def predict(self, batch, **kwargs):
        annotations = []
        for prompt_item in batch:
            ann_collection = dl.AnnotationCollection()
            for prompt_name, prompt_content in prompt_item.get('prompts').items():
                content_parts = []
                instructions_list = list()
                for partial_prompt in prompt_content:
                    mimetype = partial_prompt.get('mimetype', '')
                    value = partial_prompt.get('value', '')
                    
                    if '/image' in mimetype:
                        item_id = value.split("/stream")[0].split("/items/")[-1]
                        image_buffer = dl.items.get(item_id=item_id).download(save_locally=False).getvalue()
                        content_parts.append(Image.from_bytes(image_buffer))
                    elif '/text' in mimetype:
                        content_parts.append(value)
                    else:
                        logger.warning(
                            f"Prompt from type {mimetype} is not supported. Please provide either an image and/or a text prompt.")

                parameters = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_token,
                    "top_p": self.top_p,
                    "top_k": self.top_k
                }

                instructions_list.append(self.context)

                generative_multimodal_model = GenerativeModel(
                    self.model_name,
                    system_instruction=instructions_list
                )
                response = generative_multimodal_model.generate_content(
                    content_parts,
                    generation_config=parameters
                )
                if response._raw_response.candidates[0].finish_reason != FinishReason.STOP:
                    logger.warning(f"Generation stopped by the model. Finish reason: {response._raw_response.candidates[0].finish_reason}")
                    continue

                ann_collection.add(
                    annotation_definition=dl.FreeText(text=response.text),
                    prompt_id=prompt_name,
                    model_info={
                        'name': self.model_entity.name,
                        'model_id': self.model_entity.id,
                        'confidence': 1.0
                    }
                )
            annotations.append(ann_collection)
        return annotations
