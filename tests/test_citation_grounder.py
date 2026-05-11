from app.extraction.llm.citation_grounder import PageTokens, ground


def _tokens(words_and_boxes):
    return [{"text": w, "bbox": list(b)} for w, b in words_and_boxes]


def test_ground_finds_exact_match():
    page = PageTokens(
        page_number=1,
        tokens=_tokens(
            [
                ("Submittal", (10, 10, 60, 20)),
                ("Number:", (62, 10, 100, 20)),
                ("09", (104, 10, 120, 20)),
                ("30", (122, 10, 138, 20)),
                ("00-001", (140, 10, 180, 20)),
            ]
        ),
    )
    res = ground(page, "09 30 00-001")
    assert res is not None
    assert res.page == 1
    assert res.bbox == (104, 10, 180, 20)


def test_ground_rejects_low_overlap():
    page = PageTokens(
        page_number=2,
        tokens=_tokens([("hello", (0, 0, 10, 10)), ("world", (12, 0, 22, 10))]),
    )
    res = ground(page, "completely different quote")
    assert res is None
