import React, { useEffect, useMemo, useRef, useState } from 'react';
import UploadPanel from './components/UploadPanel';
import ResultsTable from './components/ResultsTable';
import FailuresTable from './components/FailuresTable';
import RetryDialog from './components/RetryDialog';
import {
  FailureItem,
  ResultItem,
  StatusResponse,
  downloadCsv,
  getFailures,
  getResults,
  getStatus,
  retryToken,
  uploadFiles,
  OcrBackend
} from './api';

const pageSize = 10;

const App: React.FC = () => {
  const [dbFile, setDbFile] = useState<File | null>(null);
  const [pdfFiles, setPdfFiles] = useState<File[]>([]);
  const [ocrBackend, setOcrBackend] = useState<OcrBackend>('yomitoku');
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [progress, setProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<ResultItem[]>([]);
  const [failures, setFailures] = useState<FailureItem[]>([]);
  const [activeTab, setActiveTab] = useState<'results' | 'failures'>('results');
  const [search, setSearch] = useState('');
  const [resultPage, setResultPage] = useState(1);
  const [failurePage, setFailurePage] = useState(1);
  const [retryTokenValue, setRetryTokenValue] = useState<string>('');
  const [showRetry, setShowRetry] = useState(false);
  const completedRef = useRef(false);

  useEffect(() => {
    if (!taskId) return;
    completedRef.current = false;
    setIsProcessing(true);
    const interval = setInterval(async () => {
      try {
        const statusData = await getStatus(taskId);
        setStatus(statusData);
        setProgress(statusData.progress);
        if (statusData.progress >= 100 && !completedRef.current) {
          completedRef.current = true;
          clearInterval(interval);
          const [resultsData, failuresData] = await Promise.all([
            getResults(taskId),
            getFailures(taskId)
          ]);
          setResults(resultsData);
          setFailures(failuresData);
          setIsProcessing(false);
        }
      } catch (err: any) {
        clearInterval(interval);
        setIsProcessing(false);
        setError(err?.message || 'ステータス取得に失敗しました。Poppler と OCR 依存関係を確認してください。');
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [taskId]);

  const handleStart = async () => {
    if (!dbFile || pdfFiles.length === 0) return;
    setError(null);
    setResults([]);
    setFailures([]);
    setStatus(null);
    setProgress(0);
    setResultPage(1);
    setFailurePage(1);
    setActiveTab('results');

    try {
      const response = await uploadFiles(dbFile, pdfFiles, ocrBackend);
      setTaskId(response.task_id);
    } catch (err: any) {
      setError(err?.message || 'アップロードに失敗しました。');
    }
  };

  const handleRetry = (token: string) => {
    setRetryTokenValue(token);
    setShowRetry(true);
  };

  const filteredResults = useMemo(() => {
    if (!search) return results;
    const keyword = search.toUpperCase();
    return results.filter((row) =>
      [row.pdf_name, row.token, row.hinban, row.kidou, row.zaiko]
        .filter(Boolean)
        .some((value) => value?.toString().toUpperCase().includes(keyword))
    );
  }, [results, search]);

  const filteredFailures = useMemo(() => {
    if (!search) return failures;
    const keyword = search.toUpperCase();
    return failures.filter((row) =>
      [row.pdf_name, row.token]
        .some((value) => value.toUpperCase().includes(keyword))
    );
  }, [failures, search]);

  const resultSlice = useMemo(() => {
    const start = (resultPage - 1) * pageSize;
    return filteredResults.slice(start, start + pageSize);
  }, [filteredResults, resultPage]);

  const failureSlice = useMemo(() => {
    const start = (failurePage - 1) * pageSize;
    return filteredFailures.slice(start, start + pageSize);
  }, [filteredFailures, failurePage]);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#F8FAFC' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '18px 40px',
          backgroundColor: '#FFFFFF',
          boxShadow: '0 2px 12px rgba(0,0,0,0.08)'
        }}
      >
        <div style={{ fontWeight: 600, fontSize: 20, color: '#1D4ED8' }}>AI見積OCRシステム</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 14, color: '#4B5563' }}>OCRエンジン</span>
          <select
            value={ocrBackend}
            onChange={(e) => setOcrBackend(e.target.value as OcrBackend)}
            style={{
              padding: '8px 12px',
              borderRadius: 12,
              border: '1px solid #CBD5F5',
              fontSize: 14,
              backgroundColor: '#F8FAFC'
            }}
          >
            <option value="yomitoku">YomiToku (デフォルト利用)</option>
            <option value="rapidocr">RapidOCR</option>
            <option value="paddleocr">PaddleOCR</option>
          </select>
        </div>
      </header>

      <main style={{ display: 'flex', gap: 32, padding: '28px 40px' }}>
        <UploadPanel
          dbFile={dbFile}
          pdfFiles={pdfFiles}
          ocrBackend={ocrBackend}
          status={status}
          progress={progress}
          isProcessing={isProcessing}
          onDbSelect={(file) => setDbFile(file)}
          onPdfSelect={(files) => setPdfFiles(files)}
          onBackendChange={(backend) => setOcrBackend(backend)}
          onStart={handleStart}
          error={error}
        />

        <section style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: 16,
              boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}
          >
            <div style={{ display: 'flex', gap: 12 }}>
              <button
                onClick={() => setActiveTab('results')}
                style={{
                  padding: '8px 16px',
                  borderRadius: 12,
                  border: 'none',
                  fontWeight: 600,
                  backgroundColor: activeTab === 'results' ? '#1D4ED8' : '#E5E7EB',
                  color: activeTab === 'results' ? '#FFFFFF' : '#374151',
                  cursor: 'pointer'
                }}
              >
                結果一覧
              </button>
              <button
                onClick={() => setActiveTab('failures')}
                style={{
                  padding: '8px 16px',
                  borderRadius: 12,
                  border: 'none',
                  fontWeight: 600,
                  backgroundColor: activeTab === 'failures' ? '#1D4ED8' : '#E5E7EB',
                  color: activeTab === 'failures' ? '#FFFFFF' : '#374151',
                  cursor: 'pointer'
                }}
              >
                失敗一覧
              </button>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <input
                placeholder="キーワード検索"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setResultPage(1);
                  setFailurePage(1);
                }}
                style={{
                  padding: '8px 12px',
                  borderRadius: 12,
                  border: '1px solid #CBD5F5',
                  fontSize: 14
                }}
              />
              {taskId && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    onClick={() => downloadCsv(taskId, 'results')}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 12,
                      border: 'none',
                      backgroundColor: '#1D4ED8',
                      color: '#FFFFFF',
                      cursor: 'pointer'
                    }}
                  >
                    結果CSVをダウンロード
                  </button>
                  <button
                    onClick={() => downloadCsv(taskId, 'failures')}
                    style={{
                      padding: '8px 12px',
                      borderRadius: 12,
                      border: '1px solid #1D4ED8',
                      color: '#1D4ED8',
                      backgroundColor: '#FFFFFF',
                      cursor: 'pointer'
                    }}
                  >
                    失敗CSVをダウンロード
                  </button>
                </div>
              )}
            </div>
          </div>

          {activeTab === 'results' ? (
            <ResultsTable
              data={resultSlice}
              page={resultPage}
              pageSize={pageSize}
              total={filteredResults.length}
              onPageChange={setResultPage}
            />
          ) : (
            <FailuresTable
              data={failureSlice}
              page={failurePage}
              pageSize={pageSize}
              total={filteredFailures.length}
              onPageChange={setFailurePage}
              onRetry={handleRetry}
              backendUsed={status?.backend_used}
            />
          )}
        </section>
      </main>

      <RetryDialog
        isOpen={showRetry}
        token={retryTokenValue}
        onClose={() => setShowRetry(false)}
        onSubmit={async (token) => {
          if (!taskId) return [];
          const res = await retryToken(taskId, token);
          return res.candidates;
        }}
      />
    </div>
  );
};

export default App;
