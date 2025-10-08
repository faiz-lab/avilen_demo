import React, { useCallback } from 'react';
import ProgressBar from './ProgressBar';
import StatsCards from './StatsCards';
import { OcrBackend, StatusResponse } from '../api';

interface Props {
  dbFile: File | null;
  pdfFiles: File[];
  ocrBackend: OcrBackend;
  status: StatusResponse | null;
  progress: number;
  isProcessing: boolean;
  onDbSelect: (file: File) => void;
  onPdfSelect: (files: File[]) => void;
  onBackendChange: (backend: OcrBackend) => void;
  onStart: () => void;
  error: string | null;
}

const panelStyle: React.CSSProperties = {
  width: 360,
  backgroundColor: '#FFFFFF',
  borderRadius: 16,
  boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
  padding: 24,
  display: 'flex',
  flexDirection: 'column',
  gap: 20
};

const sectionTitle: React.CSSProperties = {
  fontWeight: 600,
  fontSize: 15
};

const dropZoneStyle: React.CSSProperties = {
  border: '2px dashed #93C5FD',
  borderRadius: 12,
  padding: '18px 16px',
  textAlign: 'center' as const,
  color: '#1D4ED8',
  backgroundColor: '#EFF6FF',
  cursor: 'pointer'
};

const UploadPanel: React.FC<Props> = ({
  dbFile,
  pdfFiles,
  ocrBackend,
  status,
  progress,
  isProcessing,
  onDbSelect,
  onPdfSelect,
  onBackendChange,
  onStart,
  error
}) => {
  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      if (event.dataTransfer.files && event.dataTransfer.files.length > 0) {
        const dropped = Array.from(event.dataTransfer.files);
        const pdfs = dropped.filter((file) => file.type === 'application/pdf');
        if (pdfs.length) {
          onPdfSelect([...pdfFiles, ...pdfs]);
        }
      }
    },
    [onPdfSelect, pdfFiles]
  );

  return (
    <div style={panelStyle}>
      <div>
        <div style={sectionTitle}>マスタCSV</div>
        <label style={{ ...dropZoneStyle, display: 'block', marginTop: 12 }}>
          <input
            type="file"
            accept=".csv"
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) onDbSelect(file);
            }}
          />
          ファイル選択（CSV をドラッグ＆ドロップまたはクリック）
        </label>
        {dbFile && (
          <div style={{ marginTop: 8, fontSize: 13, color: '#374151' }}>
            {dbFile.name} ({(dbFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
      </div>

      <div>
        <div style={sectionTitle}>図面・仕様PDF</div>
        <label
          style={{ ...dropZoneStyle, display: 'block', marginTop: 12 }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept="application/pdf"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => {
              const files = e.target.files ? Array.from(e.target.files) : [];
              if (files.length) onPdfSelect([...pdfFiles, ...files]);
            }}
          />
          PDFをドラッグ＆ドロップまたはクリックで追加
        </label>
        {pdfFiles.length > 0 && (
          <ul style={{ marginTop: 8, paddingLeft: 16, fontSize: 13, color: '#374151' }}>
            {pdfFiles.map((file) => (
              <li key={file.name}>{file.name}</li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <div style={sectionTitle}>OCRエンジン</div>
        <select
          value={ocrBackend}
          onChange={(e) => onBackendChange(e.target.value as OcrBackend)}
          style={{
            width: '100%',
            padding: '10px 12px',
            borderRadius: 12,
            border: '1px solid #CBD5F5',
            fontSize: 14,
            marginTop: 10
          }}
        >
          <option value="yomitoku">YomiToku (デフォルト利用)</option>
          <option value="rapidocr">RapidOCR</option>
          <option value="paddleocr">PaddleOCR</option>
        </select>
      </div>

      <div>
        <button
          onClick={onStart}
          disabled={isProcessing || !dbFile || pdfFiles.length === 0}
          style={{
            width: '100%',
            padding: '12px 0',
            borderRadius: 12,
            border: 'none',
            fontWeight: 600,
            fontSize: 15,
            backgroundColor: isProcessing || !dbFile || pdfFiles.length === 0 ? '#9CA3AF' : '#1D4ED8',
            color: '#FFFFFF',
            cursor: isProcessing || !dbFile || pdfFiles.length === 0 ? 'not-allowed' : 'pointer',
            transition: 'background 0.2s ease'
          }}
        >
          処理を開始する
        </button>
        <div style={{ marginTop: 12 }}>
          <ProgressBar progress={progress} />
          <div style={{ fontSize: 13, color: '#6B7280', marginTop: 8 }}>
            進捗: {progress}% {status ? `(全${status.pages}ページ)` : ''}
          </div>
        </div>
        {error && (
          <div style={{ marginTop: 8, color: '#DC2626', fontSize: 13 }}>{error}</div>
        )}
      </div>

      <div>
        <div style={sectionTitle}>統計サマリー</div>
        <StatsCards
          totals={status?.totals || { tokens: 0, hit_hinban: 0, hit_spec: 0, fail: 0 }}
          backendUsed={status?.backend_used}
        />
      </div>
    </div>
  );
};

export default UploadPanel;
