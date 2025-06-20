
export async function fetchFiles() {
  const res = await fetch('http://localhost:5000/files/');
  if (!res.ok) throw new Error('Failed to fetch files');
  const files = await res.json();
  // Format the data for the FilesTab component
  return files.map(file => ({
    id: file.id,
    name: file.file_path.split(/[\\/]/).pop().replace(/\.[^/.]+$/, ''),
    type: file.file_extension.toUpperCase(),
    size: file.meta_data?.size || 'Unknown',
    uploaded: file.created_at ? file.created_at.split('T')[0] : '',
    ...file,
  }));
}

export async function deleteFile(id) {
  const res = await fetch(`http://localhost:5000/files/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error('Failed to delete file');
  }
}