# Vertex AI Model Adapters

Welcome to the repository for Dataloop model adapters that utilize Google Vertex AI models. Follow the instructions below to set up and use these adapters effectively.

For more information on Vertex AI models, refer to the [official documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models).

## Supported Models

- **Gemini 1.5 Pro**
- **Chat Bison 2**

## Setting Up Your GCP Project

To use these models, you need a Google Cloud Platform (GCP) project. Follow these steps to get started:

### 1. Enable the Vertex AI API
   - Navigate to the API Library in the GCP Console.
   - Enable the Vertex AI API.

### 2. Create a Service Account
   - Go to the IAM & Admin section in the GCP Console.
   - Create a new service account.
   - Generate a new key and download the service account JSON file.

### 3. Assign Permissions
   - Grant the service account the `aiplatform.endpoints.predict` permission.

## Integrating Google Vertex AI with Dataloop Platform

### 1. Install the Model
   - Visit the [Dataloop Marketplace](https://docs.dataloop.ai/docs/marketplace).
   - Install the desired model.

### 2. Create the Integration Service Account
   - Go to the [Data Governance](https://docs.dataloop.ai/docs/overview-1?highlight=data%20governance) section in the Dataloop platform.
   - Click on "Create Integration".
   - Choose an integration name, select "GCP" as the provider, and "Private Key" as the integration type.
   - Import the service account JSON file you previously downloaded.

### 3. Configure the Service in Data Governance
   - Add the integration to the model's [service configuration](https://docs.dataloop.ai/docs/service-runtime#secrets-for-faas) by specifying the integration name you created.

---

For additional assistance or inquiries, please refer to the Dataloop documentation or contact support.
