import os
import base64
import json
import dtlpy as dl
import logging
from vertexai.preview.generative_models import GenerativeModel, Image
from google.cloud import storage

logger = logging.getLogger("Vertex AI Adapter")


class ModelAdapter(dl.BaseModelAdapter):
    def __init__(self, model_entity: dl.Model, integration_name):
        super().__init__(model_entity)

        self.max_token = self.model_entity.configuration.get('max_token', 1024)
        self.temperature = self.model_entity.configuration.get('temperature', 0.2)
        self.top_p = self.model_entity.configuration.get('top_p', 0.7)
        self.top_k = self.model_entity.configuration.get('top_k', 40)
        self.context = self.model_entity.configuration.get('system_prompt', '')
        self.model_name = self.model_entity.configuration.get('model_name', "gemini-1.5-pro-001")

        credentials = os.environ.get(integration_name.replace('-', '_'))

        # for case of integration
        credentials = base64.b64decode(credentials)
        credentials = credentials.decode("utf-8")
        credentials = json.loads(credentials)
        credentials = json.loads(credentials['content'])
        self.client = storage.Client.from_service_account_info(info=credentials)

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
                instructions_list = list()
                text = None
                image = None
                for partial_prompt in prompt_content:
                    if 'image' in partial_prompt.get('mimetype', ''):
                        image_url = partial_prompt.get('value', '')
                        item_id = image_url.split("/stream")[0].split("/items/")[-1]
                        image_buffer = dl.items.get(item_id=item_id).download(save_locally=False).getvalue()
                        image = Image.from_bytes(image_buffer)

                    elif 'text' in partial_prompt.get('mimetype', ''):
                        text = partial_prompt.get('value')
                    else:
                        logger.warning(
                            f"Prompt from type {partial_prompt.get('mimetype', '')} is not supported either an image "
                            f"or a text prompt.")
                if text is None or image is None:
                    logger.warning(f"{prompt_name} is missing either an image or a text prompt.")
                    continue

                parameters = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_token,
                    "top_p": self.top_p,
                    "top_k": self.top_k
                }

                instructions_list.append(self.context)

                generative_multimodal_model = GenerativeModel(self.model_name,
                                                              system_instruction=instructions_list
                                                              )
                response = generative_multimodal_model.generate_content([text, image],
                                                                        generation_config=parameters)

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
    adapter = ModelAdapter(model, '')
    adapter.predict_items(items=[item])
