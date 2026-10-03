import pandas as pd
import numpy as np

# --- 1. Tai Du Lieu ---
file_path = r'D:\PYTHON\Dataset\Data\2. DU LIEU TAI CHINH DOANH NGHIEP\online+retail+ii\online_retail_II.xlsx'
try:
    df_cleaned = pd.read_excel(file_path)
    print('Da tai du lieu thanh cong tu sheet mac dinh.')
except ValueError as e:
    if 'Multiple sheets found' in str(e):
        print('Phat hien nhieu sheet. Dang doc sheet Year 2010-2011.')
        df_cleaned = pd.read_excel(file_path, sheet_name='Year 2010-2011')
    else:
        print('Loi khi tai file: {e}')

print(f'Kich thuoc ban dau cua DataFrame: {df_cleaned.shape}')

# --- 2. Thay doi ten cot (neu can) ---
print('Da kiem tra ten cot, khong doi ten mac dinh.')

# --- 3. Xoa cac hang trung lap ---
initial_rows_dup = df_cleaned.shape[0]
df_cleaned.drop_duplicates(inplace=True)
print(f'So hang sau khi xoa trung lap: {df_cleaned.shape[0]} (Da xoa {initial_rows_dup - df_cleaned.shape[0]} hang)')

# --- 4. Xu ly thieu du lieu ---
initial_rows_nan = df_cleaned.shape[0]
df_cleaned.dropna(subset=['Customer ID', 'Description'], inplace=True)
print(f'So hang sau khi xoa thieu du lieu: {df_cleaned.shape[0]} (Da xoa {initial_rows_nan - df_cleaned.shape[0]} hang)')

# --- 5. Xu ly du lieu khong hop le ---
initial_rows_invalid = df_cleaned.shape[0]
df_cleaned = df_cleaned[~df_cleaned['Invoice'].astype(str).str.contains('[A-Za-z]', na=False)]
df_cleaned = df_cleaned[df_cleaned['Quantity'] > 0]
df_cleaned = df_cleaned[df_cleaned['Price'] > 0]
print(f'So hang sau khi loai bo du lieu khong hop le: {df_cleaned.shape[0]} (Da xoa {initial_rows_invalid - df_cleaned.shape[0]} hang)')

# --- 6. Chuyen doi kieu du lieu ---
df_cleaned['InvoiceDate'] = pd.to_datetime(df_cleaned['InvoiceDate'])
df_cleaned['Quantity'] = df_cleaned['Quantity'].astype(int)
df_cleaned['Price'] = df_cleaned['Price'].astype(float)
df_cleaned['Customer ID'] = df_cleaned['Customer ID'].astype(int)
print('Da chuyen doi kieu du lieu.')

# --- 7. Tao cac cot moi ---
df_cleaned['Amount'] = df_cleaned['Quantity'] * df_cleaned['Price']
df_cleaned['Year'] = df_cleaned['InvoiceDate'].dt.year
df_cleaned['Month'] = df_cleaned['InvoiceDate'].dt.month
df_cleaned['Day'] = df_cleaned['InvoiceDate'].dt.day
df_cleaned['Hour'] = df_cleaned['InvoiceDate'].dt.hour
df_cleaned['DayOfWeek'] = df_cleaned['InvoiceDate'].dt.dayofweek
df_cleaned['MonthYear'] = df_cleaned['InvoiceDate'].dt.to_period('M')
print('Da tao cac cot tinh nang moi.')

# --- 8. Luu Tru Du Lieu Da Lam Sach ---
output_file_path = 'cleaned_online_retail.csv'
df_cleaned.to_csv(output_file_path, index=False)
print(f'Du lieu da lam sach duoc luu vao: {output_file_path}')

print('\n--- Quy trinh lam sach du lieu hoan tat! --- ')
print(df_cleaned.head())