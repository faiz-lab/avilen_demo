export interface UploadResponse {
  task_id: string;
}

export type OcrBackend = 'yomitoku' | 'rapidocr' | 'paddleocr';

export interface StatusResponse {
  progress: number;
  pages: number;
  totals: {
    tokens: number;
    matched: number;
    fail: number;
  };
  backend_used?: string;
}

export interface ResultItem {
  pdf_name: string;
  page: number;
  token: string;
  hinban?: string;
  kidou?: string;
  zaiko?: string;
}

export interface FailureItem {
  pdf_name: string;
  page: number;
  token: string;
}

export interface RetryResponse {
  candidates: string[];
}

export const uploadFiles = async (
  dbFile: File,
  pdfFiles: File[],
  ocrBackend: OcrBackend = 'yomitoku'
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('db_csv', dbFile);
  pdfFiles.forEach((file) => formData.append('pdfs', file));
  formData.append('ocr_backend', ocrBackend);

  const response = await fetch('/api/upload', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'アップロードに失敗しました。');
  }

  return response.json();
};

export const getStatus = async (taskId: string): Promise<StatusResponse> => {
  const response = await fetch(`/api/status/${taskId}`);
  if (!response.ok) {
    throw new Error('ステータス取得に失敗しました。');
  }
  return response.json();
};

export const getResults = async (taskId: string): Promise<ResultItem[]> => {
  const response = await fetch(`/api/results/${taskId}`);
  if (!response.ok) {
    throw new Error('結果の取得に失敗しました。');
  }
  return response.json();
};

export const getFailures = async (taskId: string): Promise<FailureItem[]> => {
  const response = await fetch(`/api/failures/${taskId}`);
  if (!response.ok) {
    throw new Error('失敗データの取得に失敗しました。');
  }
  return response.json();
};

export const retryToken = async (taskId: string, token: string): Promise<RetryResponse> => {
  const response = await fetch('/api/retry', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ task_id: taskId, token })
  });
  if (!response.ok) {
    throw new Error('再照合に失敗しました。');
  }
  return response.json();
};

export const downloadCsv = (taskId: string, type: 'results' | 'failures') => {
  window.open(`/api/download/${taskId}?type=${type}`, '_blank');
};
