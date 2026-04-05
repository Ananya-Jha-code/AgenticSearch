from agentic_search.models.schemas import AttributeCell, EntityRow, SourceRef
from agentic_search.pipeline.merge import merge_entity_rows


def test_merge_dedupes_normalized_names():
    a = EntityRow(
        entity_name="Foo Inc",
        attributes={
            "x": AttributeCell(value="1", sources=[SourceRef(url="http://a", quote="q1")]),
        },
    )
    b = EntityRow(
        entity_name="foo inc",
        attributes={
            "x": AttributeCell(value="1", sources=[SourceRef(url="http://b", quote="q2")]),
        },
    )
    m = merge_entity_rows([a, b])
    assert len(m) == 1
    assert len(m[0].attributes["x"].sources) == 2
