"""
Tests for the retirement pipeline (Phase 5 /shoes lifecycle reframe).

Exercised at the service level, matching the suite convention (no TestClient).
The same computation backs both the Home shoe-alerts module and the /shoes
lifecycle view, so these lock in threshold, worst-first ordering, and the
replacement-deal heuristic.
"""
from app.models.models import Deal, OwnedShoe, Retailer, Shoe
from app.services import rotation


def _owned(db, brand="Adidas", model="Adios Pro 4", *, mileage, limit,
           status="active", shoe_type=None):
    s = OwnedShoe(
        brand=brand, model=model, shoe_type=shoe_type,
        current_mileage=mileage, mileage_limit=limit, status=status,
    )
    db.add(s)
    db.flush()
    return s


def _tracked(db, brand="Nike", model="Vaporfly", *, shoe_type=None):
    s = Shoe(brand=brand, model=model, shoe_type=shoe_type, target_price=180.0)
    db.add(s)
    db.flush()
    return s


def _retailer(db, name="The Last Hunt"):
    r = Retailer(name=name, base_url="https://example.com")
    db.add(r)
    db.flush()
    return r


def _deal(db, shoe, retailer, *, is_active=True):
    d = Deal(
        shoe_id=shoe.id, retailer_id=retailer.id, current_price=150.0,
        target_price=180.0, savings_amount=50.0, savings_percent=25.0,
        product_url="https://example.com/p", is_active=is_active,
    )
    db.add(d)
    db.flush()
    return d


def test_threshold_and_worst_first_ordering(db):
    _owned(db, model="Fresh", mileage=100, limit=800)                # 12% — excluded
    _owned(db, model="Getting there", mileage=612, limit=800)        # 76.5% — in
    worst = _owned(db, model="Overdue", mileage=850, limit=800)      # 106% — worst
    _owned(db, model="No limit", mileage=900, limit=None)            # excluded (no limit)
    _owned(db, model="Retired", mileage=790, limit=800, status="retired")  # excluded
    db.commit()

    pipeline = rotation.retirement_pipeline(db)
    assert [e.shoe.model for e in pipeline] == ["Overdue", "Getting there"]
    assert pipeline[0].shoe.id == worst.id
    assert round(pipeline[0].pct, 2) == 1.06


def test_boundary_exactly_at_threshold_is_included(db):
    _owned(db, model="On the line", mileage=600, limit=800)  # exactly 75%
    db.commit()

    pipeline = rotation.retirement_pipeline(db)
    assert [e.shoe.model for e in pipeline] == ["On the line"]
    assert pipeline[0].pct == 0.75


def test_replacement_deal_count_matches_shoe_type(db):
    _owned(db, model="Worn Tempo", mileage=700, limit=800, shoe_type="tempo")
    retailer = _retailer(db)
    # Two active same-type deals → count 2.
    _deal(db, _tracked(db, model="Tempo A", shoe_type="tempo"), retailer)
    _deal(db, _tracked(db, model="Tempo B", shoe_type="tempo"), retailer)
    # A different type — must not count.
    _deal(db, _tracked(db, model="Trainer", shoe_type="daily_trainer"), retailer)
    # An inactive same-type deal — must not count.
    _deal(db, _tracked(db, model="Tempo C", shoe_type="tempo"), retailer, is_active=False)
    db.commit()

    pipeline = rotation.retirement_pipeline(db)
    assert len(pipeline) == 1
    assert pipeline[0].replacement_deals == 2


def test_untyped_shoe_has_zero_replacement_deals(db):
    _owned(db, model="Typeless", mileage=700, limit=800, shoe_type=None)
    retailer = _retailer(db)
    _deal(db, _tracked(db, model="Tempo A", shoe_type="tempo"), retailer)
    db.commit()

    pipeline = rotation.retirement_pipeline(db)
    assert len(pipeline) == 1
    assert pipeline[0].replacement_deals == 0


def test_replacement_count_is_case_insensitive_on_type(db):
    _owned(db, model="Worn Tempo", mileage=700, limit=800, shoe_type="Tempo")
    retailer = _retailer(db)
    _deal(db, _tracked(db, model="Tempo A", shoe_type="tempo"), retailer)
    db.commit()

    pipeline = rotation.retirement_pipeline(db)
    assert pipeline[0].replacement_deals == 1


def test_empty_pipeline_when_all_fresh(db):
    _owned(db, model="Fresh 1", mileage=10, limit=800)
    _owned(db, model="Fresh 2", mileage=200, limit=800)
    db.commit()

    assert rotation.retirement_pipeline(db) == []
