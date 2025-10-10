import { useState, useRef } from 'react';
import { FiUpload, FiFile, FiX, FiCheckCircle } from 'react-icons/fi';

const FileUpload = ({ onFileSelect, accept = '.csv,.xlsx,.xls' }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null); // 'uploading', 'success', 'error'
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFile = (file) => {
    const validTypes = accept.split(',').map(type => type.trim());
    const fileExtension = '.' + file.name.split('.').pop();
    
    if (!validTypes.includes(fileExtension.toLowerCase())) {
      setUploadStatus('error');
      return;
    }

    setSelectedFile(file);
    setUploadStatus('uploading');
    simulateUpload(file);
  };

  const simulateUpload = (file) => {
    // Simulate upload progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 10;
      setUploadProgress(progress);
      
      if (progress >= 100) {
        clearInterval(interval);
        setUploadStatus('success');
        if (onFileSelect) {
          onFileSelect(file);
        }
      }
    }, 200);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    setUploadStatus(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-xl p-8
            transition-all duration-300 cursor-pointer
            ${isDragging 
              ? 'border-white bg-gray-900 shadow-lg' 
              : 'border-gray-700 bg-gray-900 hover:border-gray-600 hover:bg-gray-800'
            }
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={accept}
            onChange={handleFileInput}
            className="hidden"
          />
          
          <div className="flex flex-col items-center space-y-4">
            <div className={`
              w-16 h-16 rounded-full flex items-center justify-center
              transition-all duration-300
              ${isDragging 
                ? 'bg-white scale-110' 
                : 'bg-gray-800'
              }
            `}>
              <FiUpload className={`text-3xl ${isDragging ? 'text-black' : 'text-white'}`} />
            </div>
            
            <div className="text-center">
              <p className="text-white font-medium mb-1">
                {isDragging ? 'Drop your file here' : 'Drag & Drop CSV file here'}
              </p>
              <p className="text-sm text-gray-400">
                or <span className="text-white font-medium">click to browse</span>
              </p>
            </div>
            
            <div className="flex items-center space-x-2 text-xs text-gray-400">
              <span>Supported formats:</span>
              <span className="px-2 py-1 bg-gray-800 rounded text-white">.csv</span>
              <span className="px-2 py-1 bg-gray-800 rounded text-white">.xlsx</span>
              <span className="px-2 py-1 bg-gray-800 rounded text-white">.xls</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0
                ${uploadStatus === 'success' 
                  ? 'bg-green-600' 
                  : uploadStatus === 'error'
                  ? 'bg-red-600'
                  : 'bg-gray-800'
                }
              `}>
                {uploadStatus === 'success' ? (
                  <FiCheckCircle className="text-white text-xl" />
                ) : (
                  <FiFile className="text-white text-xl" />
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-gray-400">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            
            <button
              onClick={handleRemoveFile}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <FiX className="text-gray-400 hover:text-red-500" />
            </button>
          </div>
          
          {/* Progress Bar */}
          {uploadStatus === 'uploading' && (
            <div className="mb-2">
              <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white transition-all duration-300 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1 text-right">
                {uploadProgress}%
              </p>
            </div>
          )}
          
          {/* Status Messages */}
          {uploadStatus === 'success' && (
            <div className="flex items-center space-x-2 text-green-400 text-sm">
              <FiCheckCircle />
              <span>File uploaded successfully!</span>
            </div>
          )}
          
          {uploadStatus === 'error' && (
            <div className="text-red-500 text-sm">
              <span>Invalid file type. Please upload a CSV or Excel file.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FileUpload;
