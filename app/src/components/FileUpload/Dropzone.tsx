/** @jsxImportSource @emotion/react */

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
// import './dropzone.css';
import { FileWithID } from './index';

interface DropzoneProps {
  onFilesAdded: (files: File[]) => void;
  files: FileWithID[];
  children?: React.ReactNode;
}

const Dropzone: React.FC<DropzoneProps> = ({ onFilesAdded, children }) => { 
  const onDrop = useCallback((acceptedFiles: File[]) => {
       onFilesAdded(acceptedFiles);
  }, [onFilesAdded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  const explainerText = isDragActive ?
    'Drop the files here ...' :
    'Drag \'n\' drop some files here, or click to select files';

  return (
      <div
        css={{
          color: 'black',
          border: '2px dashed #629383',
          borderRadius: '4px',
          padding: '20px',
          margin: '24px 0px 24px 0',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'rgba(98, 148, 131, 0.08)' : ''
        }}
        {...getRootProps()}
        className="dropzone"
      >
        <input {...getInputProps()} />
        { explainerText }
        { children }
      </div>
  );
}

export { Dropzone };