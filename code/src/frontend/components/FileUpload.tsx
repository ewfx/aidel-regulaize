import React, { useState, useEffect } from 'react';
import { UploadCloud, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadFile, getFileStatus } from '../services/api';
import type { FileMetadata } from '../types';
import toast from 'react-hot-toast';
import clsx from 'clsx';

export function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<FileMetadata[]>([]);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadFile(file),
    onSuccess: (data) => {
      setUploadedFiles(prev => [...prev, data]);
      toast.success('File uploaded successfully');
      // Start polling for file status
      startPolling(data.id);
    },
  });

  const startPolling = (fileId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await getFileStatus(fileId);
        setUploadedFiles(prev => 
          prev.map(file => 
            file.id === fileId ? status : file
          )
        );
        
        if (status.status === 'COMPLETED' || status.status === 'FAILED') {
          clearInterval(pollInterval);
          if (status.status === 'COMPLETED') {
            toast.success('File processing completed');
          } else {
            toast.error('File processing failed');
          }
        }
      } catch (error) {
        clearInterval(pollInterval);
        console.error('Error polling file status:', error);
      }
    }, 2000);

    // Cleanup interval after 5 minutes
    setTimeout(() => clearInterval(pollInterval), 300000);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
      uploadMutation.mutate(file);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      for (const file of files) {
        uploadMutation.mutate(file);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'FAILED':
        return 'bg-wf-red bg-opacity-20 text-wf-red';
      case 'PROCESSING':
        return 'bg-wf-gold bg-opacity-20 text-wf-black';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={clsx(
          'border-2 border-dashed rounded-lg p-12 text-center transition-colors duration-200',
          isDragging ? 'border-wf-red bg-wf-red bg-opacity-5' : 'border-wf-gray border-opacity-20'
        )}
      >
        <div className="flex flex-col items-center">
          <UploadCloud className={clsx('h-12 w-12', isDragging ? 'text-wf-red' : 'text-wf-gray')} />
          <div className="mt-4">
            <label htmlFor="file-upload" className="cursor-pointer">
              <span className="mt-2 block text-sm font-medium text-wf-black">
                Drop files here or click to upload
              </span>
              <input
                id="file-upload"
                name="file-upload"
                type="file"
                className="sr-only"
                multiple
                onChange={handleFileInput}
                accept=".json,.csv,.xlsx,.xml,.pdf,.txt"
              />
            </label>
            <p className="mt-1 text-xs text-wf-gray">
              Supported formats: JSON, CSV, Excel, XML, PDF, TXT
            </p>
          </div>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-wf-black">Uploaded Files</h3>
          </div>
          <div className="border-t border-wf-gray border-opacity-20">
            <ul className="divide-y divide-wf-gray divide-opacity-20">
              {uploadedFiles.map((file) => (
                <li key={file.id} className="px-4 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-wf-gray" />
                      <div className="ml-3">
                        <p className="text-sm font-medium text-wf-black">{file.filename}</p>
                        <p className="text-xs text-wf-gray">
                          {(file.size / 1024).toFixed(2)} KB • {file.format}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className={clsx(
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        getStatusColor(file.status)
                      )}>
                        {file.status === 'PROCESSING' && (
                          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        )}
                        {file.status}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {uploadMutation.isLoading && (
        <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl flex items-center space-x-4">
            <Loader2 className="h-6 w-6 text-wf-red animate-spin" />
            <p className="text-wf-black">Uploading file...</p>
          </div>
        </div>
      )}
    </div>
  );
}