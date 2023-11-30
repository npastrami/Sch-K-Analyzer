/** @jsxImportSource @emotion/react */

import { useState } from 'react';
import { Container } from '@mui/material';
import { v4 as uuidv4 } from 'uuid';

import { Dropzone } from './Dropzone';
import { FileList } from './FileList';

export type FileStatus = 'Pending' | 'Uploading...' | 'Extracting...' | 'Upload Completed' | 'Extract Completed' | 'Error' | "Empty Extraction";

export type FileWithID = {
  file: File
  id: string;
  path?: string | undefined;
  status: FileStatus;
  formType: "None" | "K1-1065" | "Form";
}

export const FileUpload = () => {
  const [filesToUpload, setFilesToUpload] = useState<FileWithID[]>([]);

  const handleIdentifier = (newFiles: File[]) => {
    const updatedFiles: FileWithID[] = newFiles.map((file: File) => {
      const id = uuidv4();
      return { file, id, path: file.name, status: 'Pending', formType: 'None' }; // Now each object is a FileWithID
    });
    
    setFilesToUpload(prevFiles => [...prevFiles, ...updatedFiles]);
  };

  const handleRemoveFile = (id: string) => { 
    setFilesToUpload(prevFiles => prevFiles.filter(file => file.id !== id));
  };

  return (
    <>
      <Container
        css={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '2px solid #e4e4e4',
        }}
      >
        <Dropzone onFilesAdded={handleIdentifier} files={filesToUpload}>
          <FileList files={filesToUpload} onRemove={handleRemoveFile}/>
        </Dropzone>
      </Container>
    </>
  );
}
