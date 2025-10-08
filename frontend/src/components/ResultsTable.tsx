import React from 'react';
import { ResultItem } from '../api';

interface Props {
  data: ResultItem[];
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}

const headerStyle: React.CSSProperties = {
  textAlign: 'left',
  fontSize: 13,
  color: '#6B7280',
  padding: '12px 16px',
  borderBottom: '1px solid #E5E7EB'
};

const cellStyle: React.CSSProperties = {
  fontSize: 14,
  padding: '12px 16px',
  borderBottom: '1px solid #F3F4F6'
};

const rowStyle: React.CSSProperties = {
  backgroundColor: '#FFFFFF',
  transition: 'background 0.2s ease'
};

const ResultsTable: React.FC<Props> = ({ data, page, pageSize, total, onPageChange }) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div style={{ backgroundColor: '#FFFFFF', borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
        <thead style={{ backgroundColor: '#F3F4F6' }}>
          <tr>
            <th style={headerStyle}>PDF名</th>
            <th style={headerStyle}>ページ</th>
            <th style={headerStyle}>トークン</th>
            <th style={headerStyle}>一致タイプ</th>
            <th style={headerStyle}>マッチ品番</th>
            <th style={headerStyle}>在庫情報</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr
              key={`${row.pdf_name}-${row.page}-${row.token}-${index}`}
              style={rowStyle}
              onMouseEnter={(e) => ((e.currentTarget.style.backgroundColor = '#F9FAFB'))}
              onMouseLeave={(e) => ((e.currentTarget.style.backgroundColor = '#FFFFFF'))}
            >
              <td style={cellStyle}>{row.pdf_name}</td>
              <td style={cellStyle}>{row.page}</td>
              <td style={cellStyle}>{row.token}</td>
              <td style={cellStyle}>{row.matched_type === 'hinban' ? '品番' : row.matched_type === 'spec' ? 'スペック' : '-'}</td>
              <td style={cellStyle}>{row.matched_hinban || '-'}</td>
              <td style={cellStyle}>{row.zaiko || '-'}</td>
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td style={{ ...cellStyle, textAlign: 'center' }} colSpan={6}>
                データがありません。
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', backgroundColor: '#F9FAFB' }}>
        <span style={{ fontSize: 13, color: '#6B7280' }}>
          {page} / {totalPages} ページ
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page === 1}
            style={{
              padding: '6px 12px',
              borderRadius: 12,
              border: '1px solid #CBD5F5',
              backgroundColor: page === 1 ? '#E5E7EB' : '#FFFFFF',
              cursor: page === 1 ? 'not-allowed' : 'pointer'
            }}
          >
            前へ
          </button>
          <button
            onClick={() => onPageChange(Math.min(totalPages, page + 1))}
            disabled={page === totalPages}
            style={{
              padding: '6px 12px',
              borderRadius: 12,
              border: '1px solid #CBD5F5',
              backgroundColor: page === totalPages ? '#E5E7EB' : '#FFFFFF',
              cursor: page === totalPages ? 'not-allowed' : 'pointer'
            }}
          >
            次へ
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultsTable;
