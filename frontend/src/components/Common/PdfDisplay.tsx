import React from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import { Button, Box } from '@chakra-ui/react';
import { DownloadIcon } from '@chakra-ui/icons';

interface PdfDisplayProps {
  base64String: string | null;
  fileName?: string; // New prop for custom file name
}

export const PdfDisplay: React.FC<PdfDisplayProps> = ({ base64String, fileName = 'document.pdf' }) => {
  const pdfBlob = base64String ? `data:application/pdf;base64,${base64String}` : null;

  const sanitizeFileName = (str: string) => {
    return str
      .replace(/[^a-z0-9]/gi, '_') // Replace any character that's not alphanumeric with underscore
      .replace(/_+/g, '_')         // Replace multiple consecutive underscores with a single one
      .toLowerCase()               // Convert to lowercase
      .trim();                     // Remove leading and trailing whitespace
  };

  const sanitizedFileName = sanitizeFileName(fileName);


  const handleDownload = () => {
    if (pdfBlob) {
      const link = document.createElement('a');
      link.href = pdfBlob;
      link.download = sanitizedFileName; // Use the provided fileName or default to 'document.pdf'
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Box>
      <Box mb={4}>
      </Box>
      <Box style={{ width: '100%', height: '70vh', border: '1px solid black' }}>
        {pdfBlob ? (
          <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
            <Viewer fileUrl={pdfBlob} />
          </Worker>
        ) : (
          <p>No PDF available</p>
        )}
      </Box>
      <Button
        leftIcon={<DownloadIcon />}
        onClick={handleDownload}
        isDisabled={!pdfBlob}
      >
        Download {sanitizedFileName} {/* Display the file name in the button text */}
      </Button>
    </Box>
  );
};
