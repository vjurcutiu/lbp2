import React, { useEffect, useState, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFiles } from './services/fileFetch';
import { processFolder } from '../../services/folderApi';
import uploadTrackingService from '../../features/uploadTracking/uploadTrackingService';
import { resetUpload } from '../../features/uploadTracking/uploadTrackingSlice';

const Filters = ({ setFilter }) => (
  <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
    <button onClick={() => setFilter('all')}>All</button>
    <button onClick={() => setFilter('PDF')}>PDF</button>
    <button onClick={() => setFilter('IMAGE')}>Image</button>
    <button onClick={() => setFilter('TEXT')}>Text</button>
  </div>
);

const FileDetails = ({ file }) => (
  <div style={{
    background: '#e6e9ef',
    borderRadius: '1rem',
    padding: '2rem 1rem',
    minWidth: '220px',
    maxWidth: '220px',
    height: '100%',
    boxShadow: '2px 0 8px rgba(0,0,0,0.05)'
  }}>
    {file ? (
      <>
        <h4>{file.name}</h4>
        <p><b>Type:</b> {file.type}</p>
        <p><b>Size:</b> {file.size}</p>
        <p><b>Uploaded:</b> {file.uploaded}</p>
      </>
    ) : (
      <p style={{ color: '#777' }}>Select a file to see details.</p>
    )}
  </div>
);

const FilesTab = () => {
  const dispatch = useDispatch();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);

  // Redux slice for upload tracking
  const { uploadedFiles, failedFiles, totalFiles, isComplete } = useSelector(
    state => state.uploadTracking
  );

  // Track currently uploading file names locally for spinner display
  const [uploadingFiles, setUploadingFiles] = useState([]);

  const folderInputRef = useRef();

  useEffect(() => {
    fetchFiles().then(setFiles).finally(() => setLoading(false));
    // Clear any previous upload tracking when tab loads
    dispatch(resetUpload());
  }, [dispatch]);

  // When Redux tells us files are uploaded, remove spinners
  useEffect(() => {
    // Remove any uploadingFiles that are now in uploadedFiles or failedFiles
    setUploadingFiles(prev =>
      prev.filter(
        name => !uploadedFiles.includes(name) && !failedFiles.map(f => f.fileName).includes(name)
      )
    );
    // On upload complete, refresh the files list
    if (isComplete) fetchFiles().then(setFiles);
  }, [uploadedFiles, failedFiles, isComplete]);

  // Folder select handler
  const handleFolderChange = async (event) => {
    const filesList = Array.from(event.target.files);

    if (!filesList.length) return;

    // We'll get fake paths like C:\fakepath\Folder\File.txt for browsers; you may need Electron for true folders.
    // Here we simulate folder name extraction for demo purposes.
    const folderPath = filesList[0].webkitRelativePath
      ? filesList[0].webkitRelativePath.split('/')[0]
      : '';

    if (!folderPath) {
      alert('Please select an entire folder (not individual files)');
      return;
    }

    // List all files to be uploaded
    setUploadingFiles(filesList.map(f => f.name));

    try {
      // Extensions can be derived or set statically; here just .txt/.pdf for demo
      const sessionId = await processFolder(folderPath, ['.txt', '.pdf']);
      uploadTrackingService.connect(sessionId);
    } catch (err) {
      alert('Failed to process folder: ' + err.message);
      setUploadingFiles([]);
    }
    // Reset the input for re-uploading same folder
    event.target.value = '';
  };

  const filteredFiles = files.filter(
    file =>
      (filter === 'all' || file.type === filter) &&
      file.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div>Loading files…</div>;

  return (
    <div style={{
      padding: '2rem',
      background: '#f7f7f7',
      minHeight: '100vh',
      fontFamily: 'Inter, sans-serif'
    }}>
      {/* Input Bar */}
      <input
        type="text"
        placeholder="Search files..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{
          width: '100%',
          padding: '0.8rem 1rem',
          borderRadius: '1rem',
          border: '1px solid #ddd',
          fontSize: '1.1rem',
          marginBottom: '1rem'
        }}
      />
      {/* Upload Folder Button */}
      <div style={{ marginBottom: '1rem' }}>
        <button
          onClick={() => folderInputRef.current.click()}
          style={{
            padding: '0.6rem 1.2rem',
            borderRadius: '1rem',
            border: 'none',
            background: '#8d99ae',
            color: 'white',
            fontWeight: 'bold',
            cursor: 'pointer'
          }}
        >
          Upload Folder
        </button>
        <input
          type="file"
          webkitdirectory="true"
          directory=""
          multiple
          ref={folderInputRef}
          style={{ display: 'none' }}
          onChange={handleFolderChange}
        />
      </div>
      {/* Filters */}
      <Filters setFilter={setFilter} />
      {/* Main Content */}
      <div style={{
        display: 'flex',
        gap: '2rem',
        marginTop: '1.5rem',
        height: '480px'
      }}>
        {/* Details Bar */}
        <FileDetails file={selected} />
        {/* Files List */}
        <div style={{
          flex: 1,
          background: '#fff',
          borderRadius: '1rem',
          boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
          padding: '2rem',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Files</h3>
          {filteredFiles.length > 0 ? (
            filteredFiles.map(file => (
              <div
                key={file.id}
                onClick={() => setSelected(file)}
                style={{
                  padding: '1rem',
                  borderRadius: '0.8rem',
                  background: selected?.id === file.id ? '#dde5ff' : 'transparent',
                  cursor: 'pointer',
                  marginBottom: '0.7rem',
                  transition: 'background 0.2s',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <span>{file.name}</span>
                {/* Spinner while uploading, check by name */}
                {uploadingFiles.includes(file.name) && (
                  <span style={{ marginLeft: '0.7rem' }}>
                    <Spinner />
                  </span>
                )}
              </div>
            ))
          ) : (
            <div style={{ color: '#888', fontStyle: 'italic' }}>No files found.</div>
          )}
        </div>
      </div>
    </div>
  );
};

const Spinner = () => (
  <span style={{
    display: 'inline-block',
    width: '18px',
    height: '18px',
    border: '3px solid #bbb',
    borderTop: '3px solid #3498db',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  }} />
);

if (typeof window !== "undefined" && !document.getElementById("global-spinner-keyframes")) {
  const style = document.createElement("style");
  style.id = "global-spinner-keyframes";
  style.textContent = `
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}

export default FilesTab;
