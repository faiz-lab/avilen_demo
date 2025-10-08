import React from 'react';

interface Props {
  progress: number;
}

const ProgressBar: React.FC<Props> = ({ progress }) => {
  return (
    <div style={{ backgroundColor: '#E5E7EB', borderRadius: 12, overflow: 'hidden', height: 12 }}>
      <div
        style={{
          width: `${progress}%`,
          backgroundColor: '#1D4ED8',
          height: '100%',
          transition: 'width 0.6s ease'
        }}
      />
    </div>
  );
};

export default ProgressBar;
