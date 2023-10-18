import React, { useState } from "react";
import axios from "axios";
import { useDropzone } from "react-dropzone";
import uploadReceiptIcon from "./upload-receipt.png";
import uploadInvoiceIcon from "./upload-invoices.png";
//import uploadInvoiceIcon from "./upload-invoices.png";
import SampleImageComponent from "./ModalComponent";

const FileUpload = ({ uploadType }) => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fileUrl, setFileUrl] = useState(null);

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(
        `http://127.0.0.1:5001/upload/${uploadType}`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setFileUrl(URL.createObjectURL(new Blob([response.data])));
      setUploadedFile(file);
    } catch (error) {
      console.error("Error uploading file:", error);
    } finally {
      setLoading(false);
    }
  };

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: ["image/*", "application/pdf"],
  });

  const getFileExtension = (uploadType) => {
    // Define mappings of uploadType to file extensions
    const extensions = {
      receipts: "csv", // Change to the appropriate extension for receipts
      invoices: "csv", // Change to the appropriate extension for invoices
    };
    return extensions[uploadType] || "txt"; // Default to "txt" if not found
  };

  const downloadFileName = uploadedFile
    ? `${uploadedFile.name}.${getFileExtension(uploadType)}`
    : "";

  return (
    <div className="file-upload">
      <div {...getRootProps()} className="dropzone">
        <input {...getInputProps()} />
        {loading ? (
          <p>Loading...</p>
        ) : uploadedFile ? (
          <div className="file-preview">
            <p>Uploaded: {uploadedFile.name}</p>
          </div>
        ) : (
          <>
            {uploadType === "receipts" ? (
              <img
                src={uploadReceiptIcon}
                alt="Upload Receipt"
                className="upload-icon"
              />
            ) : (
              <>
               <SampleImageComponent/>
              <img
                src={uploadInvoiceIcon}
                alt="Upload Invoice"
                className="upload-icon"
              />
              </>
            )}
            <p>
              Drag & drop a {uploadType} file here, or click to select a file
            </p>
          </>
        )}
      </div>
      {fileUrl && (
        <div className="download-area">
          <a
            href={fileUrl}
            download={downloadFileName}
            className="download-link"
          >
            Download File
          </a>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
