# Vertex AI Model Adapters

Welcome to the repository for Dataloop model adapters that utilize Google Vertex AI models. Follow the instructions below to set up and use these adapters effectively.

For more information on Vertex AI models, refer to the [official documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models).

## Supported Models

- **Gemini 1.5 Pro**

## Setting Up Your GCP Project

To use these models, you need a Google Cloud Platform (GCP) project. Follow these steps to get started:

### 1. Enable the Vertex AI API
   - Navigate to the API Library in the GCP Console.
   - Enable the Vertex AI API.

### 2. Create a [Service Account](https://docs.dataloop.ai/docs/private-key-integration?highlight=create%20service%20account)
   - Go to the IAM & Admin section in the GCP Console.
   - Create a new service account.
   - Generate a new key and download the service account JSON file.

### 3. Assign Permissions
   - Grant the service account the `aiplatform.endpoints.predict` permission.

## Integrating Google Vertex AI with Dataloop Platform

   - Visit the [Dataloop Marketplace](https://docs.dataloop.ai/docs/marketplace), under Models tab.
![Marketplace](assets/marketplace.png)
   - Select the model and click on "Install" and then "Proceed".
![Add Integration](assets/add_integration.png)
   - Select an existing GCP integration or add a new one by importing the JSON file you previously downloaded.
![Create Integration](assets/create_integration.png)
   - Install the model.
![Install](assets/add_integration_to_app.png)

### Use the model and change model's configuration

- This model is using prompt items as input. You can find more information about prompt items [here](https://developers.dataloop.ai/tutorials/annotations/prompts/chapter).
- Go to 'Models' page.
![Model Page](assets/models_page.png)
- Select the model configuration you want to update.  
  ![Model Parameters](assets/model_parameters.png)

- Here, you can change parameters for your model under 'Configuration':
  - **"model_name"**: Model version from [Vertex AI Gemini Generative models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference).
  - **"system_prompt"**: The context for the generative model (e.g., "Talk like a pirate").
  - **"max_tokens"**: The maximum number of tokens (words or pieces of words) that the model is allowed to generate in a single response.
  - **"temperature"**: A parameter that controls the randomness of the output. Lower values make the output more focused and deterministic, while higher values increase randomness and creativity.
  - **"top_p"**: Also known as nucleus sampling. It controls the cumulative probability distribution of the next token. Tokens are selected from the smallest set whose cumulative probability exceeds this threshold, leading to more coherent responses.
  - **"top_k"**: Limits the number of highest probability tokens to consider when generating the next token. Lower values restrict the choice to a smaller set of top tokens, making responses more focused.

---

### Attributions

This application, developed by Dataloop, provides an adapter for Google Vertex AI Generative AI models. While the code in this repository is open-sourced under the Apache License 2.0, the use of Google Vertex AI Generative AI models is subject to Google's licensing terms, including but not limited to:

- [Google Cloud Platform Terms of Service](https://cloud.google.com/terms)
- [Vertex AI Terms of Service](https://cloud.google.com/terms/service-terms#vertex_ai_models)

### Important Note

By using this application with Google Vertex AI Generative AI models, you acknowledge that:
1. You have reviewed and agreed to Google's licensing terms for the use of Vertex AI services.
2. You are solely responsible for ensuring compliance with these terms when using Google Vertex AI Generative AI models.
3. The authors of this application, Dataloop, are not responsible for any compliance issues, fees, or damages arising from the use of Google Vertex AI models.

This application is provided "as is" under the terms of the Apache License 2.0. Dataloop makes no warranties or guarantees regarding the performance, functionality, or legal compliance of this adapter when used with Google Vertex AI Generative AI models.

### Additional Resources

For more information about the Google Vertex AI Generative AI models, please visit the official documentation:
- [Google Vertex AI Generative AI Models](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models)

For additional assistance or inquiries, please refer to the Dataloop documentation or contact support.
