import os
import base64
import json
import dtlpy as dl
import logging
from vertexai.language_models import ChatModel
import vertexai
from google.oauth2 import service_account

logger = logging.getLogger("Vertex AI Adapter")


class ModelAdapter(dl.BaseModelAdapter):
    def __init__(self, model_entity: dl.Model, integration_name):
        super().__init__(model_entity)

        self.max_token = self.model_entity.configuration.get('max_token', 1024)
        self.temperature = self.model_entity.configuration.get('temperature', 0.2)
        self.top_p = self.model_entity.configuration.get('top_p', 0.7)
        self.top_k = self.model_entity.configuration.get('top_k', 40)
        self.context = self.model_entity.configuration.get('system_prompt', None)
        self.model_name = self.model_entity.configuration.get('model_name', 'chat-bison@002')

        # Retrieving the service account JSON file, formatting it and initializing Vertex with it
        credentials = os.environ.get(integration_name)
        credentials = base64.b64decode(credentials)
        credentials = credentials.decode("utf-8")
        credentials = json.loads(credentials)
        credentials = json.loads(credentials['content'])
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
                text = None
                context = None
                for partial_prompt in prompt_content:
                    if 'text' in partial_prompt.get('mimetype', ''):
                        text = partial_prompt.get('value')
                    else:
                        logger.warning(
                            f"Prompt Type: {partial_prompt.get('mimetype', '')}. Only text prompt from type is "
                            f"supported.")
                if text is None:
                    logger.warning(f"{prompt_name} is missing a text prompt.")
                    continue

                parameters = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_token,
                    "top_p": self.top_p,
                    "top_k": self.top_k
                }

                chat_model = ChatModel.from_pretrained(self.model_name)
                chat = chat_model.start_chat(
                    context=self.context if self.context else None,
                )
                response = chat.send_message(
                    text, **parameters
                )

                content = response.text
                ann_collection.add(
                    annotation_definition=dl.FreeText(text=content),
                    prompt_id=prompt_name,
                    model_info={
                        'name': self.model_entity.name,
                        'model_id': self.model_entity.id,
                        'confidence': 1.0
                    }
                )
            annotations.append(ann_collection)
        return annotations


if __name__ == '__main__':
    model = dl.models.get(model_id='')
    item = dl.items.get(item_id='')
    adapter = ModelAdapter(model)
    adapter.predict_items(items=[item])
