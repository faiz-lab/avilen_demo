import React from 'react';

interface StatItem {
  title: string;
  value: number;
}

interface Props {
  totals: {
    tokens: number;
    matched: number;
    fail: number;
  };
  backendUsed?: string;
}

const cardStyle: React.CSSProperties = {
  backgroundColor: '#FFFFFF',
  borderRadius: 12,
  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  padding: '16px 18px',
  marginBottom: 12
};

const titleStyle: React.CSSProperties = {
  fontSize: 13,
  color: '#6B7280',
  marginBottom: 6
};

const valueStyle: React.CSSProperties = {
  fontSize: 22,
  fontWeight: 600,
  color: '#1D4ED8'
};

const footerStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#6B7280',
  marginTop: 8
};

const StatsCards: React.FC<Props> = ({ totals, backendUsed }) => {
  const stats: StatItem[] = [
    { title: '抽出トークン数', value: totals.tokens },
    { title: '照合成功', value: totals.matched },
    { title: '失敗', value: totals.fail }
  ];

  return (
    <div>
      {stats.map((stat) => (
        <div key={stat.title} style={cardStyle}>
          <div style={titleStyle}>{stat.title}</div>
          <div style={valueStyle}>{stat.value}</div>
        </div>
      ))}
      <div style={footerStyle}>使用エンジン：{backendUsed ?? '—'}</div>
    </div>
  );
};

export default StatsCards;
