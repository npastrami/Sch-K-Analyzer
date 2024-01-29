import React from "react";
import { FileStatus, FileWithID } from "./index";

interface ProcessResult {
  status: string;
}

export class FileProcessor {
  constructor(
    public clientID: string,
    public versionID: string,
    public files: FileWithID[],
    public setFiles: React.Dispatch<React.SetStateAction<FileWithID[]>>
  ) {}

  async processFiles(): Promise<void> {
    const formData = new FormData();
    this.files.forEach((file) => {
      formData.append("files[]", file.file);
      formData.append("formTypes[]", file.formType ?? "");
    });
    formData.append("clientID", this.clientID);
    formData.append("versionID", this.versionID);

    this.files.forEach((file) => {
      if (file.formType !== "None") {
        this.setFileStatus(file.id, FileStatus.Extracting);
      }  else {
            this.setFileStatus(file.id, FileStatus.Uploading);
      }
    });

    try {
      const response = await fetch("/api/process_doc", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Server responded with an error.");
      }

      const results: ProcessResult[] = await response.json();

      results.forEach((result: ProcessResult, index: number) => {
        const file = this.files[index];
        this.setFileStatus(file.id, result.status as FileStatus);
      });
    } catch (error) {
      this.files.forEach((file) => {
        this.setFileStatus(file.id, FileStatus.Error);
      });
      console.error("An error occurred during file processing:", error);
    }
  }

  async setFileStatus(id: string, status: FileStatus): Promise<void> {
    this.setFiles((prevFiles) => {
      return prevFiles.map((f) => (f.id === id ? { ...f, status } : f));
    });
  }

  async startProcessing(): Promise<void> {
    await this.processFiles();
  }
}
