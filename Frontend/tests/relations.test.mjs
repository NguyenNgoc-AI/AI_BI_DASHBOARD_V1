import test from 'node:test';
import assert from 'node:assert/strict';
import { readRelationFiles, relationPayload, describeRelation } from '../relations.mjs';

const file = (name, text) => ({ name, size: new TextEncoder().encode(text).length, text: async () => text });
test('reads Olist-style names and builds API contract', async () => {
  const tables = await readRelationFiles([
    file('olist_orders_dataset.csv', 'order_id,customer_id\nO1,C1\n'),
    file('olist_customers_dataset.json', '[{"customer_id":"C1"}]'),
  ]);
  assert.deepEqual(tables.map(t => t.name), ['orders', 'customers']);
  assert.equal(tables[0].rows.length, 1);
  const payload = relationPayload(tables, tables.map(t => t.name));
  assert.equal(payload.tables.orders[0].customer_id, 'C1');
  assert.throws(() => relationPayload(tables, ['same', 'same']), /trùng/);
  assert.throws(() => relationPayload(tables, ['', 'customers']), /Tên bảng/);
});
test('rejects single, oversized, unsupported and invalid files', async () => {
  await assert.rejects(readRelationFiles([]), /2 đến 10/);
  await assert.rejects(readRelationFiles([{size:104857600},{size:1}]), /100 MiB/);
  await assert.rejects(readRelationFiles([file('bad.json','[]'),file('ok.csv','a\n1')]), /bad.json/);
  await assert.rejects(readRelationFiles([file('bad.xlsx','x'),file('ok.csv','a\n1')]), /CSV và JSON/);
});

test('explains repeated and missing relationship keys without asserting all rows match', () => {
  const link = {child_table:'orders',child_column:'customer_id',parent_table:'customers',parent_column:'customer_id'};
  const result = describeRelation(link, [{name:'orders',rows:[{customer_id:'C1'},{customer_id:'C1'},{customer_id:null}]}]);
  assert.equal(result.title,'Đơn hàng liên kết với Khách hàng');
  assert.equal(result.matched,2);
  assert.equal(result.missing,1);
  assert.match(result.type,/Nhiều/);
  assert.match(describeRelation(link,[{name:'orders',rows:[{customer_id:'C1'}]}]).type,/Một dòng/);
});
