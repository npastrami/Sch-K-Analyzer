import React from "react";
import { FileStatus, FileWithID } from ".";

export class FileProcessor {
  clientID: string;
  versionID: string;
  files: FileWithID[];
  setFiles: React.Dispatch<React.SetStateAction<FileWithID[]>>;

  constructor(
    clientID: string,
    versionID: string,
    files: FileWithID[],
    setFiles: React.Dispatch<React.SetStateAction<FileWithID[]>>
  ) {
    this.clientID = clientID;
    this.versionID = versionID;
    this.files = files;
    this.setFiles = setFiles;
  }

  async uploadFile(file: FileWithID): Promise<any> {
    const formData = new FormData();
    formData.append("file", file.file);
    formData.append("clientID", this.clientID);
    formData.append("versionID", this.versionID);
    formData.append("docType", file.formType);  
  
    const response = await fetch("/upload", {  
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.message || "Unknown server error");
    }

    return await response.json();
  }

  async extractData(file: FileWithID): Promise<any> {
    const response = await fetch("/extract_k1_1065", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        clientID: this.clientID,
        versionID: this.versionID,
        fileID: file.id,
        blobName: file.file.name,
      }),
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.message || "Unknown server error");
    }

    return await response.json();
  }

  async setFileStatus(id: string, status: FileStatus): Promise<void> {
    this.setFiles((prevFiles) => {
      return prevFiles.map((f) => (f.id === id ? { ...f, status } : f));
    });
  }

  async processEachFile(file: FileWithID): Promise<void> {
      await this.setFileStatus(file.id, "Uploading...");
      await this.uploadFile(file); 
      if (file.formType === "None") {
        await this.setFileStatus(file.id, "Upload Completed");
      } else if (file.formType === "K1-1065") {
        await this.setFileStatus(file.id, "Extracting...");
        const extractedData = await this.extractData(file);
        if (extractedData.isEmpty) {
          await this.setFileStatus(file.id, "Empty Extraction");
        } else {
          await this.setFileStatus(file.id, "Extract Completed");
        }
      } else {
        await this.setFileStatus(file.id, "Error");
      }    
  }

  async startProcessing(): Promise<void> {
    const promises = this.files.map((file) => this.processEachFile(file));
    await Promise.allSettled(promises);
  }
}