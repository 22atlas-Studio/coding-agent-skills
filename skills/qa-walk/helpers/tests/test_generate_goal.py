from generate_goal import generate_goal


def test_generate_goal_matches_golden(fixtures_dir):
    workflow = {
        "id": "dealer-offer-accept",
        "name": "Dealer accepts customer offer",
        "persona": "dealer",
        "entry_route": "/dealer/deals/{deal_id}",
        "test_data": {"deal_id": "42"},
        "definition_of_done": (
            "Dealer sees incoming customer offer on the deal page, clicks Accept,\n"
            "deal status flips from OFFER_PENDING to ACCEPTED, the badge updates\n"
            "without a hard reload, POST /api/notifications fires once, and zero\n"
            "console errors appear in the page lifecycle.\n"
        ),
        "do_not_change": (
            "Don't navigate away from this deal. Don't touch other deals.\n"
            "Don't modify dealer profile settings.\n"
        ),
        "regression_checks": [
            "Accept button is not stuck disabled when offer is pending (bug from run 2026-04-28-1430)",
            "Status badge updates without a full page reload (bug from run 2026-05-03-1100)",
        ],
    }
    persona = {"email": "operator@example.test"}
    actual = generate_goal(app="example-app", workflow=workflow, persona=persona)
    expected = (fixtures_dir / "expected_goal_dealer_offer_accept.md").read_text()
    assert actual.strip() == expected.strip()


def test_generate_goal_omits_empty_regression_checks_section():
    workflow = {
        "id": "x", "name": "X", "persona": "p", "entry_route": "/x",
        "test_data": {},
        "definition_of_done": "Just do it.",
        "do_not_change": "Nothing.",
        "regression_checks": [],
    }
    out = generate_goal(app="a", workflow=workflow, persona={"email": "e@e"})
    assert "Regression checks" not in out


def test_generate_goal_resolves_route_placeholders():
    workflow = {
        "id": "x", "name": "X", "persona": "p", "entry_route": "/x/{id}",
        "test_data": {"id": "99"},
        "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": [],
    }
    out = generate_goal(app="a", workflow=workflow, persona={"email": "e@e"})
    assert "Entry route: /x/99" in out


def test_generate_goal_resolves_from_fixture_via_qa_dir(tmp_path):
    """`from-fixture` translates to the value in qa/fixtures.yaml."""
    (tmp_path / "fixtures.yaml").write_text(
        "fixtures:\n  deal_id: 00000000-0000-4000-a000-000000000020\n"
    )
    workflow = {
        "id": "x", "name": "X", "persona": "p",
        "entry_route": "/deals/deal/{deal_id}",
        "test_data": {"deal_id": "from-fixture"},
        "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": [],
    }
    out = generate_goal(
        app="a", workflow=workflow, persona={"email": "e@e"}, qa_dir=tmp_path
    )
    assert "Entry route: /deals/deal/00000000-0000-4000-a000-000000000020" in out


def test_generate_goal_from_fixture_without_fixtures_yaml_raises(tmp_path):
    """`from-fixture` without a fixtures.yaml entry is a hard error."""
    import pytest
    workflow = {
        "id": "x", "name": "X", "persona": "p", "entry_route": "/x/{id}",
        "test_data": {"id": "from-fixture"},
        "definition_of_done": "..", "do_not_change": "..",
        "regression_checks": [],
    }
    with pytest.raises(KeyError, match="from-fixture"):
        generate_goal(
            app="a", workflow=workflow, persona={"email": "e@e"}, qa_dir=tmp_path
        )
