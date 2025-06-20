
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFiles } from './services/fileFetch';
import { processFolder } from '../../services/folderApi';
import uploadTrackingService from '../uploadTracking/uploadTrackingService';
import { resetUpload } from '../uploadTracking/uploadTrackingSlice';
import Filters from './Filters';
import FileDetails from './FileDetails';
import FilesList from './FilesList';
import FolderBrowseButton from '../../components/sidebar/FolderBrowseButton';

const FilesTab = () => {
  const dispatch = useDispatch();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [optimisticFiles, setOptimisticFiles] = useState([]);

  const { uploadedFiles, failedFiles, isComplete } = useSelector(
    state => state.uploadTracking
  );
  const [uploadingFiles, setUploadingFiles] = useState([]);

  useEffect(() => {
    fetchFiles().then(setFiles).finally(() => setLoading(false));
    dispatch(resetUpload());
  }, [dispatch]);

  useEffect(() => {
    setUploadingFiles(prev =>
      prev.filter(
        name => !uploadedFiles.includes(name) && !failedFiles.map(f => f.fileName).includes(name)
      )
    );
    if (isComplete) fetchFiles().then(setFiles);
  }, [uploadedFiles, failedFiles, isComplete]);

  // Remove optimistic file if it is confirmed by backend (matching id)
  useEffect(() => {
    if (files.length === 0 || optimisticFiles.length === 0) return;
    const backendIds = new Set(files.map(f => f.id));
    setOptimisticFiles(prev => prev.filter(f => !backendIds.has(f.id)));
  }, [files]);

  const handleFolderSelect = async (folderPathOrFiles) => {
    let selectedPaths = [];
    if (Array.isArray(folderPathOrFiles)) {
      selectedPaths = folderPathOrFiles;
    } else if (typeof folderPathOrFiles === 'string') {
      selectedPaths = [folderPathOrFiles];
    } else if (folderPathOrFiles && folderPathOrFiles[0]) {
      selectedPaths = Array.from(folderPathOrFiles).map(f => f.path || f.name);
    }

    // Add optimistic files to state
    setOptimisticFiles(prev => [
      ...selectedPaths.map(path => ({
        id: path,
        name: path.split(/[\\/]/).pop(),
        status: 'pending',
      })),
      ...prev
    ]);

    setUploadingFiles(selectedPaths);

    // Use the first path as folderPath for backend
    const folderPath = selectedPaths[0];
    try {
      const sessionId = await processFolder(folderPath, ['.txt', '.pdf']);
      uploadTrackingService.connect(sessionId);
    } catch (err) {
      alert('Failed to process folder: ' + err.message);
      setUploadingFiles([]);
    }
  };

  const filteredFiles = files.filter(
    file =>
      (filter === 'all' || file.type === filter) &&
      file.name.toLowerCase().includes(search.toLowerCase())
  );

  // Merge optimistic files (those not already in backend) to the top
  const backendFileIds = new Set(files.map(f => f.id));
  const displayedFiles = [
    ...optimisticFiles.filter(f => !backendFileIds.has(f.id)),
    ...filteredFiles
  ];

  if (loading) return <div>Loading files…</div>;

  return (
    <div style={{
      padding: '2rem',
      background: '#f7f7f7',
      minHeight: '100vh',
      fontFamily: 'Inter, sans-serif'
    }}>
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
      <div style={{ marginBottom: '1rem' }}>
        <FolderBrowseButton
          onFolderSelect={handleFolderSelect}
          buttonText="Add Files"
          onError={err => alert('File selection error: ' + err.message)}
        />
      </div>
      <Filters setFilter={setFilter} />
      <div style={{
        display: 'flex',
        gap: '2rem',
        marginTop: '1.5rem',
        height: '480px'
      }}>
        <FileDetails file={selected} />
        <FilesList
          files={displayedFiles}
          selected={selected}
          setSelected={setSelected}
        />
      </div>
    </div>
  );
};

export default FilesTab;
