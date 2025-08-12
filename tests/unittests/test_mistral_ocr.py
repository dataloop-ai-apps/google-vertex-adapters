import dtlpy as dl
from adapters.mistral_ocr.mistral_ocr import ModelAdapter


def prd():
    dataset = project.datasets.get(dataset_id='')
    item_json = dataset.items.get(item_id='')
    items = [item_json]
    adapter.predict_items(items=items, with_upload=True)


if __name__ == '__main__':
    # dl.login()
    # dl.setenv('rc')

    project = dl.projects.get(project_id='')

    model_entity = dl.models.get(model_id="")
    model_entity.model_artifacts = []

    adapter = ModelAdapter(model_entity=model_entity)

    prd()
