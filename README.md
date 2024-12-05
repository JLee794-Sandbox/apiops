This repository contains the API artifacts for APIOps, defining the API Management (APIM) configuration and utilities.

## Repository Structure

- **apimartifacts**: This directory contains the configuration files for API Management.
- **utils**: This directory holds example policies and a demo Python Jupyter notebook to showcase APIM GenAI capabilities.

### apimartifacts

The `apimartifacts` directory includes all necessary configuration files to set up and manage your API Management instance. These files typically include API definitions, policies, and other configuration settings required to deploy and maintain your APIs within the APIM service.

#### Publishing and Pulling Configurations

To publish and pull configurations using the pipelines stored in the `.github/workflows` directory:

1. **Publishing Configurations**: [run-publisher.yaml](.github/workflows/run-publisher.yaml)
    - Ensure your changes to the configuration files in the `apimartifacts` directory are committed to your branch.
    - Trigger the publishing pipeline by pushing your changes to the repository. The pipeline will automatically deploy the updated configurations to your APIM instance.

2. **Pulling Configurations**: [run-extractor.yaml](.github/workflows/run-extractor.yaml)
    - Use the pull pipeline to fetch the latest configurations from your APIM instance.
    - This can be done by triggering the pull pipeline manually or through a scheduled run, ensuring your local repository is always in sync with the deployed configurations.

### utils

The `utils` directory provides:
- Example policies to help you get started with API Management. These policies can be used as templates or references to create custom policies tailored to your specific needs.
- A demo Python Jupyter notebook that demonstrates the capabilities of APIM GenAI. This notebook includes sample code and explanations to help you understand how to leverage APIM GenAI features in your API management workflows.

## How to Use

1. **Explore the `apimartifacts` Directory**:
    - Navigate to the `apimartifacts` directory to find the configuration files.
    - Review and modify these files as needed to match your API Management requirements.
    - Deploy the configuration files to your APIM instance using the appropriate deployment tools or scripts.

2. **Utilize the `utils` Directory**:
    - Check out the example policies in the `utils` directory to understand how to implement common API Management scenarios.
    - Use the demo Python Jupyter notebook to experiment with APIM GenAI capabilities. Follow the instructions in the notebook to run the code and observe the results.
    - Adapt the provided examples to fit your specific use cases and integrate them into your APIOps workflow.

Feel free to explore the directories and use the provided resources to enhance your APIOps workflow.