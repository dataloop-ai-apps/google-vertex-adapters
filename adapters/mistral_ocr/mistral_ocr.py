import os
import base64
import json
import dtlpy as dl
import logging
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

logger = logging.getLogger("Vertex Mistral OCR Adapter")


class ModelAdapter(dl.BaseModelAdapter):
    def __init__(self, model_entity: dl.Model):
        super().__init__(model_entity)
        
    def _get_access_token(self):
        """Get a fresh access token"""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def load(self, local_path, **kwargs):
        self.model_id = self.model_entity.configuration.get('model_id', 'mistral-ocr-2505')
        
        # Get GCP credentials using the same pattern as Gemini
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
        self.region = credentials.get('location', 'us-central1')  # Default region if not specified
        
        # Create credentials and get access token
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.credentials.refresh(Request())

    def prepare_item_func(self, item: dl.Item):
        """Prepare items for OCR processing - handles both direct files and prompt items"""
        # Check if it's a prompt item (JSON with dltype='prompt')
        if ('json' in item.mimetype and 
            item.metadata.get('system', dict()).get('shebang', dict()).get('dltype') == 'prompt'):
            buffer = json.load(item.download(save_locally=False))
            return buffer
        
        # Check if it's a direct image or PDF file
        elif (item.mimetype.startswith('image/') or item.mimetype.startswith('application/pdf')):
            return item
        
        # Unsupported item type
        else:
            logger.warning(f"Item mimetype {item.mimetype} is not supported. "
                          f"Please provide either a prompt item (JSON) or direct image/PDF files.")
            return None

    def _process_file_item(self, item: dl.Item):
        """Process a direct file item (image or PDF)"""
        try:
            # Download item and convert to base64
            item_buffer = item.download(save_locally=False)
            item_data = item_buffer.getvalue()
            base64_document = base64.b64encode(item_data).decode('utf-8')
            
            # Determine document type for the data URL
            if item.mimetype.startswith('image/'):
                if 'jpeg' in item.mimetype or 'jpg' in item.mimetype:
                    data_url = f"data:image/jpeg;base64,{base64_document}"
                elif 'png' in item.mimetype:
                    data_url = f"data:image/png;base64,{base64_document}"
                else:
                    data_url = f"data:{item.mimetype};base64,{base64_document}"
            elif item.mimetype.startswith('application/pdf'):
                data_url = f"data:application/pdf;base64,{base64_document}"
            else:
                logger.warning(f"Unsupported mimetype: {item.mimetype}")
                return None
                
            return self._call_mistral_ocr_api(data_url, item.id)
            
        except Exception as e:
            logger.error(f"Error processing file item {item.id}: {str(e)}")
            return None

    def _process_prompt_item(self, prompt_item, prompt_name):
        """Process a prompt item to extract image/PDF content"""
        try:
            for partial_prompt in prompt_item:
                mimetype = partial_prompt.get('mimetype', '')
                value = partial_prompt.get('value', '')
                
                # Handle image content in prompt
                if 'image' in mimetype:
                    item_id = value.split("/stream")[0].split("/items/")[-1]
                    image_buffer = dl.items.get(item_id=item_id).download(save_locally=False).getvalue()
                    base64_document = base64.b64encode(image_buffer).decode('utf-8')
                    
                    # Determine image type
                    if 'jpeg' in mimetype or 'jpg' in mimetype:
                        data_url = f"data:image/jpeg;base64,{base64_document}"
                    elif 'png' in mimetype:
                        data_url = f"data:image/png;base64,{base64_document}"
                    else:
                        data_url = f"data:{mimetype};base64,{base64_document}"
                    
                    return self._call_mistral_ocr_api(data_url, item_id)
                
                # Handle PDF content in prompt
                elif 'application/pdf' in mimetype:
                    item_id = value.split("/stream")[0].split("/items/")[-1]
                    pdf_buffer = dl.items.get(item_id=item_id).download(save_locally=False).getvalue()
                    base64_document = base64.b64encode(pdf_buffer).decode('utf-8')
                    data_url = f"data:application/pdf;base64,{base64_document}"
                    
                    return self._call_mistral_ocr_api(data_url, item_id)
                else:
                    logger.warning(f"Prompt mimetype {mimetype} is not supported for OCR. "
                                 f"Please provide image or PDF content.")
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"Error processing prompt item {prompt_name}: {str(e)}")
            return None

    def _call_mistral_ocr_api(self, data_url, item_id):
        """Make API call to Mistral OCR service"""
        try:
            # Prepare API request
            url = f"https://{self.region}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.region}/publishers/mistralai/models/{self.model_id}:rawPredict"
            
            headers = {
                "Authorization": f"Bearer {self._get_access_token()}",
                "Accept": "application/json",
            }
            
            payload = {
                "model": self.model_id,
                "document": {
                    "type": "document_url",
                    "document_url": data_url,
                }
            }
            
            # Make API request
            response = requests.post(url=url, headers=headers, json=payload)
            
            if response.status_code == 200:
                try:
                    response_dict = response.json()
                    
                    # Extract OCR text from all pages
                    ocr_text = ""
                    if 'pages' in response_dict:
                        for page in response_dict['pages']:
                            if 'markdown' in page:
                                ocr_text += page['markdown'] + "\n\n"
                    
                    return ocr_text.strip() if ocr_text.strip() else None
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON response for item {item_id}: {e}")
                    logger.error(f"Raw response: {response.text}")
                    return None
            else:
                logger.error(f"OCR request failed for item {item_id} with status code: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Mistral OCR API for item {item_id}: {str(e)}")
            return None

    def predict(self, batch, **kwargs):
        annotations = []
        
        for batch_item in batch:
            ann_collection = dl.AnnotationCollection()
            
            # Handle direct file items (images/PDFs)
            if isinstance(batch_item, dl.Item):
                ocr_text = self._process_file_item(batch_item)
                
                if ocr_text:
                    batch_item.description = ocr_text
                else:
                    logger.warning(f"No OCR text extracted from item {batch_item.id}")
            
            # Handle prompt items
            elif isinstance(batch_item, dict) and 'prompts' in batch_item:
                for prompt_name, prompt_content in batch_item.get('prompts').items():
                    ocr_text = self._process_prompt_item(prompt_content, prompt_name)
                    
                    if ocr_text:
                        ann_collection.add(
                            annotation_definition=dl.FreeText(text=ocr_text),
                            prompt_id=prompt_name,
                            model_info={
                                'name': self.model_entity.name,
                                'model_id': self.model_entity.id,
                                'confidence': 1.0
                            }
                        )
                    else:
                        logger.warning(f"No OCR text extracted from prompt {prompt_name}")
            
            else:
                logger.error(f"Unsupported batch item type: {type(batch_item)}")
            
            annotations.append(ann_collection)
            
        return annotations