export async function fetchFiles() {
  const res = await fetch('http://localhost:5000/files/');
  if (!res.ok) throw new Error('Failed to fetch files');
  const files = await res.json();
  return files.map(file => {
    let topics = {};
    if (file.meta_data?.keywords) {
      try {
        const raw = JSON.parse(file.meta_data.keywords);
        Object.entries(raw).forEach(([k, v]) => {
          if (k !== 'keywords') { // Ignore general keywords
            topics[k] = v;
          }
        });
      } catch {
        topics = {};
      }
    }
    return {
      id: file.id,
      name: file.file_path.split(/[\\/]/).pop().replace(/\.[^/.]+$/, ''),
      type: file.file_extension.toUpperCase(),
      size: file.meta_data?.size || 'Unknown',
      uploaded: file.created_at ? file.created_at.split('T')[0] : '',
      topics,
      ...file,
    };
  });
}

export async function deleteFile(id) {
  const res = await fetch(`http://localhost:5000/files/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error('Failed to delete file');
  }
}

export async function fetchFileContent(path) {
  const res = await fetch(`http://localhost:5000/files/content?path=${encodeURIComponent(path)}`);
  if (!res.ok) throw new Error('Failed to load file content');
  const data = await res.json();
  return data.content;
}