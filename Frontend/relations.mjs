import { parseDataset } from './core.mjs';

export async function readRelationFiles(files) {
  if (files.length < 2 || files.length > 10)
    throw new Error('Chọn từ 2 đến 10 tệp CSV/JSON để tìm liên kết.');
  if (files.some(f => !f.size) || files.reduce((sum, f) => sum + f.size, 0) > 104857600)
    throw new Error('Tệp không được rỗng. Tổng dung lượng tối đa là 100 MiB.');
  const tables = [];
  for (const file of files) {
    try {
      const rows = parseDataset(await file.text(), file.name);
      const columnSet = new Set();
      for (const row of rows) for (const key of Object.keys(row)) columnSet.add(key);
      const columns = [...columnSet];
      if (columns.length > 100) throw new Error('Tối đa 100 cột mỗi bảng.');
      tables.push({ file: file.name, name: file.name.replace(/\.(csv|json)$/i, '').replace(/^olist_/, '').replace(/_dataset$/, ''), rows, columns });
    } catch (error) { throw new Error(`${file.name}: ${error.message}`); }
  }
  return tables;
}

export function relationPayload(tables, names) {
  if (tables.length < 2) throw new Error('Hãy chọn ít nhất 2 bảng trước khi phân tích.');
  const result = Object.create(null);
  tables.forEach((table, i) => {
    const name = (names[i] || '').trim();
    if (!/^[a-zA-Z][a-zA-Z0-9_]*$/.test(name))
      throw new Error('Tên bảng bắt đầu bằng chữ, chỉ gồm chữ không dấu, số và dấu gạch dưới.');
    if (Object.hasOwn(result, name)) throw new Error(`Tên bảng bị trùng: ${name}. Hãy đổi tên.`);
    result[name] = table.rows;
  });
  const payload = { tables: result };
  if (new TextEncoder().encode(JSON.stringify(payload)).length > 104857600)
    throw new Error('Dữ liệu sau chuyển đổi vượt 100 MiB. Hãy chọn các file nhỏ hơn.');
  return payload;
}

export function describeRelation(link, tables) {
  const labels = { orders: 'Đơn hàng', customers: 'Khách hàng', order_items: 'Chi tiết đơn hàng', order_payments: 'Thanh toán', order_reviews: 'Đánh giá', geolocation: 'Vị trí địa lý' };
  const child = labels[link.child_table] || `Bảng ${link.child_table}`;
  const parent = labels[link.parent_table] || `bảng ${link.parent_table}`;
  const rows = tables.find(t => t.name === link.child_table)?.rows || [];
  const values = rows.map(row => row[link.child_column]).filter(v => v != null && v !== '');
  const repeated = new Set(values.map(String)).size < values.length;
  return {
    title: `${child} liên kết với ${parent}`,
    explanation: `Mỗi dòng có mã trong ${child} tìm được một dòng tương ứng trong ${parent}. ${repeated ? `Một dòng trong ${parent} được nhiều dòng trong ${child} tham chiếu.` : 'Trong dữ liệu đã chọn, mỗi mã chỉ xuất hiện một lần ở phía bảng này.'}`,
    type: repeated ? 'Nhiều dòng liên kết với một dòng' : 'Một dòng liên kết với một dòng trong dữ liệu hiện tại',
    matched: values.length,
    missing: rows.length - values.length,
    example: link.child_table === 'orders' && link.parent_table === 'customers' ? 'Ví dụ sử dụng: tìm thành phố hoặc bang của khách đã đặt mỗi đơn hàng. Quan hệ mã trong file chưa chắc đại diện cho một người duy nhất.' : `Có thể đối chiếu thông tin giữa ${child} và ${parent} bằng cột mã chung.`,
  };
}
