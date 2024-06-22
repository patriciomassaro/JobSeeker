
import React from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';

interface PdfDisplayProps {
  base64String: string | null;
}

export const PdfDisplay: React.FC<PdfDisplayProps> = ({ base64String }) => {
  const pdfBlob = base64String ? `data:application/pdf;base64,${base64String}` : null;

  return (
    <div style={{ width: '100%', height: '100vh', border: '1px solid black' }}>
      {pdfBlob ? (
        <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
          <Viewer fileUrl={pdfBlob} />
        </Worker>
      ) : (
        <p>No PDF available</p>
      )}
    </div>
  );
};
