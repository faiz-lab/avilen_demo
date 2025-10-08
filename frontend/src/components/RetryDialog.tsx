import React, { useEffect, useState } from 'react';

interface Props {
  isOpen: boolean;
  token: string;
  onClose: () => void;
  onSubmit: (token: string) => Promise<string[]>;
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100vw',
  height: '100vh',
  backgroundColor: 'rgba(15, 23, 42, 0.35)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000
};

const dialogStyle: React.CSSProperties = {
  backgroundColor: '#FFFFFF',
  padding: '24px 28px',
  borderRadius: 16,
  width: 420,
  boxShadow: '0 12px 40px rgba(15,23,42,0.25)'
};

const RetryDialog: React.FC<Props> = ({ isOpen, token, onClose, onSubmit }) => {
  const [input, setInput] = useState(token);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setInput(token);
      setCandidates([]);
      setError(null);
    }
  }, [isOpen, token]);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await onSubmit(input);
      setCandidates(res);
      if (!res.length) {
        setError('候補が見つかりませんでした。入力内容を見直してください。');
      }
    } catch (e) {
      setError('再照合に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={overlayStyle}>
      <div style={dialogStyle}>
        <div style={{ fontWeight: 600, fontSize: 18, marginBottom: 12 }}>再照合</div>
        <div style={{ fontSize: 14, color: '#6B7280', marginBottom: 12 }}>修正したトークンを入力し、再照合を実行します。</div>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ width: '100%', padding: '10px 12px', borderRadius: 12, border: '1px solid #CBD5F5', fontSize: 14 }}
        />
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 18 }}>
          <button
            onClick={onClose}
            style={{ padding: '8px 16px', borderRadius: 12, border: '1px solid #CBD5F5', backgroundColor: '#FFFFFF', cursor: 'pointer' }}
          >
            キャンセル
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading || !input}
            style={{
              padding: '8px 18px',
              borderRadius: 12,
              border: 'none',
              backgroundColor: loading || !input ? '#9CA3AF' : '#1D4ED8',
              color: '#FFFFFF',
              cursor: loading || !input ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? '照合中...' : '再照合を実行'}
          </button>
        </div>
        {error && <div style={{ marginTop: 12, color: '#DC2626', fontSize: 13 }}>{error}</div>}
        {candidates.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 13, color: '#6B7280', marginBottom: 6 }}>候補品番:</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 14 }}>
              {candidates.map((candidate) => (
                <li key={candidate}>{candidate}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default RetryDialog;
