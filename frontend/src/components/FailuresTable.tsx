import React from 'react';
import { FailureItem } from '../api';

interface Props {
  data: FailureItem[];
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onRetry: (token: string) => void;
  backendUsed?: string;
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

const noticeStyle: React.CSSProperties = {
  backgroundColor: '#FEE2E2',
  color: '#B91C1C',
  padding: '12px 16px',
  fontSize: 13,
  fontWeight: 500,
  borderBottom: '1px solid #FCA5A5'
};

const FailuresTable: React.FC<Props> = ({ data, page, pageSize, total, onPageChange, onRetry, backendUsed }) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const trimmedBackend = backendUsed?.trim();
  const showFallbackNotice =
    !!trimmedBackend && trimmedBackend.toLowerCase() !== 'yomitoku';

  return (
    <div style={{ backgroundColor: '#FFFFFF', borderRadius: 16, boxShadow: '0 2px 12px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
      {showFallbackNotice && (
        <div style={noticeStyle}>
          ※ YomiToku が利用できなかったため {trimmedBackend} に切り替えました。
        </div>
      )}
      <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: 0 }}>
        <thead style={{ backgroundColor: '#FEE2E2' }}>
          <tr>
            <th style={headerStyle}>PDF名</th>
            <th style={headerStyle}>ページ</th>
            <th style={headerStyle}>トークン</th>
            <th style={headerStyle}>操作</th>
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={`${row.pdf_name}-${row.page}-${row.token}-${index}`}>
              <td style={{ ...cellStyle, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#DC2626', display: 'inline-block' }} />
                {row.pdf_name}
              </td>
              <td style={cellStyle}>{row.page}</td>
              <td style={cellStyle}>{row.token}</td>
              <td style={cellStyle}>
                <button
                  onClick={() => onRetry(row.token)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 12,
                    border: 'none',
                    backgroundColor: '#1D4ED8',
                    color: '#FFFFFF',
                    cursor: 'pointer'
                  }}
                >
                  再照合
                </button>
              </td>
            </tr>
          ))}
          {data.length === 0 && (
            <tr>
              <td style={{ ...cellStyle, textAlign: 'center' }} colSpan={4}>
                失敗データはありません。
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', backgroundColor: '#FEF2F2' }}>
        <span style={{ fontSize: 13, color: '#B91C1C' }}>
          {page} / {totalPages} ページ
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => onPageChange(Math.max(1, page - 1))}
            disabled={page === 1}
            style={{
              padding: '6px 12px',
              borderRadius: 12,
              border: '1px solid #FCA5A5',
              backgroundColor: page === 1 ? '#FEE2E2' : '#FFFFFF',
              color: '#B91C1C',
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
              border: '1px solid #FCA5A5',
              backgroundColor: page === totalPages ? '#FEE2E2' : '#FFFFFF',
              color: '#B91C1C',
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

export default FailuresTable;
