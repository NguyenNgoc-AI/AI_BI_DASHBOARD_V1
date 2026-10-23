import json
import pytest

from backend.dashboard_engine.data_pipeline import ingest, coerce_ecommerce_types, prepare_rows


def test_generic_preserves_ids_and_reports_missing():
    rows = ingest(b'customer_id,score\n001,4\n002,\n', 'customers.csv', generic=True)
    assert rows[0] == {'customer_id': '001', 'score': 4.0}
    assert rows[1]['score'] is None
    assert prepare_rows([{'a': 1}, {'b': 2}])[0]['b'] is None


@pytest.mark.parametrize('rows', [
    [{'Revenue': 1, 'revenue': 2}], [{'a': {'nested': 1}}],
    [{f'col{i}': i for i in range(101)}], [{'a': float('inf')}], [], [{}],
])
def test_reject_invalid_table(rows):
    with pytest.raises(ValueError):
        ingest(json.dumps(rows).encode(), 'test.json', generic=True)


@pytest.mark.parametrize('body', [b'a,b\n1,2,3\n', b'a,b\n1\n', b'a,a\n1,2\n'])
def test_reject_bad_csv(body):
    with pytest.raises(ValueError):
        ingest(body, 'test.csv', generic=True)


@pytest.mark.parametrize('field,value', [('order_id', None), ('product', ''), ('revenue', True), ('quantity', -2), ('new_customers', 0.5), ('ad_spend', -1)])
def test_strict_business_validation(field, value):
    row = dict(date='2026-10-01', order_id='A1', product='Pen', revenue=100, cost=60)
    row[field] = value
    with pytest.raises(ValueError):
        coerce_ecommerce_types([row])


def test_limits_and_duplicate_json_keys():
    with pytest.raises(ValueError):
        ingest(b'[{"a":1,"a":2}]', 'test.json', generic=True)
    with pytest.raises(ValueError):
        ingest(b'a\n1\n2\n', 'test.csv', max_rows=1, generic=True)
