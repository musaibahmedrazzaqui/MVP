import React from "react";
import "./fileUpload.css";
import FileUpload from "./FileUpload";

function App() {
  return (
    <div className="App">
      <h1 style={{ fontSize: 50 }}>File Upload App</h1>
      <div className="file-upload-container">
        <FileUpload uploadType="receipts" />
        <FileUpload uploadType="invoices" />
      </div>
      <h2 style={{ fontSize: 30 }}>
        Reload the page to use the service again!
      </h2>
    </div>
  );
}

export default App;
