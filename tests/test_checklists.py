import pytest

from checklists import CONTRACT_TYPES, LANGUAGES, load_checklist


@pytest.mark.parametrize("contract_type", CONTRACT_TYPES)
def test_every_item_has_all_labels_and_keywords(contract_type):
    for item in load_checklist(contract_type)["items"]:
        for language in LANGUAGES:
            assert item["label"].get(language, "").strip(), f"{item['id']} has no {language} label"
        assert isinstance(item.get("keywords"), list)