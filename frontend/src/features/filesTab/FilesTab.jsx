import React, { useEffect, useState, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchFiles, deleteFile } from './services/fileFetch';
import { processFolder } from '../../services/folderApi';
import uploadTrackingService from '../uploadTracking/uploadTrackingService';
import { resetUpload } from '../uploadTracking/uploadTrackingSlice';
import Filters from './Filters';
import FileDetails from './FileDetails';
import FilesList from './FilesList';
import FolderBrowseButton from '../../components/sidebar/FolderBrowseButton';
import FileViewerModal from './FileViewerModal';

const FilesTab = () => {
  const dispatch = useDispatch();
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [optimisticFiles, setOptimisticFiles] = useState([]);
  const [viewerPath, setViewerPath] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedKeyword, setSelectedKeyword] = useState(null);

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
    const backendPaths = new Set(files.map(f => f.file_path));
    setOptimisticFiles(prev => prev.filter(f => !backendPaths.has(f.id)));
  }, [files]);

  // Sync optimistic file status with Redux upload tracking
  useEffect(() => {
    if (optimisticFiles.length === 0) return;
    setOptimisticFiles(prev => prev.map(file => {
      if (uploadedFiles.includes(file.name)) {
        return { ...file, status: 'complete' };
      }
      const failed = failedFiles.find(f => f.fileName === file.name);
      if (failed) {
        return { ...file, status: 'error', error: failed.error };
      }
      return file;
    }));
  }, [uploadedFiles, failedFiles]);

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
        name: path.split(/[\\/]/).pop().replace(/\.[^/.]+$/, ''),
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

  const handleDelete = async (id) => {
    try {
      await deleteFile(id);
      fetchFiles().then(setFiles);
      setOptimisticFiles(prev => prev.filter(f => f.id !== id));
    } catch (err) {
      alert('Failed to delete file: ' + err.message);
    }
  };

  // ---- Topic and Keyword Extraction for Filters ----
  const allTopics = useMemo(() => {
    const topicsSet = new Set();
    files.forEach(f => {
      if (f.topics) Object.keys(f.topics).forEach(topic => topicsSet.add(topic));
    });
    return Array.from(topicsSet);
  }, [files]);

  const keywordsForSelectedTopic = useMemo(() => {
    if (!selectedTopic) return [];
    const keywordsSet = new Set();
    files.forEach(f => {
      if (f.topics && f.topics[selectedTopic]) {
        const val = f.topics[selectedTopic];
        if (Array.isArray(val)) val.forEach(x => keywordsSet.add(x));
        else if (val) keywordsSet.add(val);
      }
    });
    return Array.from(keywordsSet);
  }, [files, selectedTopic]);

  // ---- Filtering Logic ----
  const filteredFiles = files.filter(file => {
    // Topic & keyword filter
    if (selectedTopic) {
      const values = file.topics && file.topics[selectedTopic]
        ? (Array.isArray(file.topics[selectedTopic]) ? file.topics[selectedTopic] : [file.topics[selectedTopic]])
        : [];
      if (selectedKeyword && !values.includes(selectedKeyword)) {
        return false;
      }
      if (!selectedKeyword && (!values.length || !values.some(Boolean))) {
        return false; // If topic is set but file has no value for it
      }
    }
    // Search
    if (search && !file.name.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    return true;
  });

  // ---- Sorting: order by selected topic ----
  const sortedFiles = useMemo(() => {
    if (!selectedTopic) return filteredFiles;
    return [...filteredFiles].sort((a, b) => {
      const aVal = a.topics && a.topics[selectedTopic];
      const bVal = b.topics && b.topics[selectedTopic];
      const aStr = Array.isArray(aVal) ? (aVal[0] || '') : (aVal || '');
      const bStr = Array.isArray(bVal) ? (bVal[0] || '') : (bVal || '');
      return aStr.localeCompare(bStr);
    });
  }, [filteredFiles, selectedTopic]);

  // ---- Merge optimistic files to the top ----
  const backendPaths = new Set(files.map(f => f.file_path));
  const displayedFiles = [
    ...optimisticFiles.filter(f => !backendPaths.has(f.id)).map(f => ({ ...f, onDelete: handleDelete })),
    ...sortedFiles.map(f => ({ ...f, onDelete: handleDelete }))
  ];

  if (loading) return <div>Loading files…</div>;

  return (
    <div style={{
      padding: '2rem',
      background: '#f7f7f7',
      minHeight: '100vh',
      fontFamily: 'Inter, sans-serif'
    }}>
      {viewerPath && (
        <FileViewerModal
          filePath={viewerPath}
          onClose={() => setViewerPath(null)}
        />
      )}

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
      <Filters
        topics={allTopics}
        selectedTopic={selectedTopic}
        setSelectedTopic={val => {
          setSelectedTopic(val);
          setSelectedKeyword(null); // reset keyword if topic changes
        }}
        keywords={keywordsForSelectedTopic}
        selectedKeyword={selectedKeyword}
        setSelectedKeyword={setSelectedKeyword}
      />
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
          onDoubleClick={setViewerPath}
        />
      </div>
    </div>
  );
};

export default FilesTab;